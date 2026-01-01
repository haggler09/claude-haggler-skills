#!/usr/bin/env python3
"""
Snowflake query execution script.
Supports multiple authentication methods and output formats.

Usage:
    uvx --with snowflake-connector-python python query.py --query "SELECT 1"
    uvx --with snowflake-connector-python --with tabulate python query.py -q "SELECT *" --format table
"""

import os
import sys
import json
import argparse
import csv
import io
import re
import base64
import time
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import date, datetime
from decimal import Decimal

# Snowflake connector (required)
try:
    import snowflake.connector
    from snowflake.connector import DictCursor
    from snowflake.connector.errors import (
        DatabaseError,
        ProgrammingError,
        InterfaceError,
        OperationalError,
    )
except ImportError:
    print(
        json.dumps(
            {
                "status": "error",
                "error_code": "MISSING_DEPENDENCY",
                "error_message": "snowflake-connector-python is required. "
                "Run with: uvx --with snowflake-connector-python python query.py ...",
            }
        ),
        file=sys.stderr,
    )
    sys.exit(1)

# Cryptography for key-pair auth (optional, bundled with snowflake-connector)
try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# Tabulate for table output (optional)
try:
    from tabulate import tabulate

    HAS_TABULATE = True
except ImportError:
    HAS_TABULATE = False


# Constants
DEFAULT_LIMIT = 100
DEFAULT_TIMEOUT = 300
REQUIRED_ENV_VARS = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER"]

# Error codes
ERROR_CODES = {
    "MISSING_ENV_VAR": "Required environment variable not set",
    "MISSING_QUERY": "No query provided (use --query or --file)",
    "FILE_NOT_FOUND": "SQL file not found",
    "INVALID_OPTION": "Invalid command line option",
    "AUTH_FAILED": "Authentication failed",
    "INVALID_PRIVATE_KEY": "Failed to load private key",
    "NO_AUTH_METHOD": "No authentication method configured",
    "CONNECTION_FAILED": "Failed to connect to Snowflake",
    "QUERY_ERROR": "Query execution failed",
    "OUTPUT_WRITE_FAILED": "Failed to write output file",
    "FORMAT_NOT_SUPPORTED": "Output format requires additional dependency",
}


def json_serializer(obj: Any) -> Any:
    """Custom JSON serializer for non-standard types."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return base64.b64encode(obj).decode("utf-8")
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def output_error(
    error_code: str,
    message: str,
    details: Optional[Dict[str, Any]] = None,
    file=sys.stderr,
) -> None:
    """Output error in JSON format."""
    error = {
        "status": "error",
        "error_code": error_code,
        "error_message": message,
    }
    if details:
        error["details"] = details
    print(json.dumps(error, indent=2, default=json_serializer), file=file)


def detect_auth_method() -> Tuple[str, Dict[str, Any]]:
    """
    Detect authentication method from environment variables.

    Returns:
        Tuple of (auth_method_name, auth_params_dict)
    """
    authenticator = os.getenv("SNOWFLAKE_AUTHENTICATOR", "").lower()

    # SSO/OAuth authentication
    if authenticator == "externalbrowser":
        return "sso", {"authenticator": "externalbrowser"}

    if authenticator == "oauth":
        token = os.getenv("SNOWFLAKE_OAUTH_TOKEN")
        if token:
            return "oauth", {"authenticator": "oauth", "token": token}

    # Key-pair authentication
    key_path = os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH")
    key_raw = os.getenv("SNOWFLAKE_PRIVATE_KEY_RAW")

    if key_path or key_raw:
        if not HAS_CRYPTO:
            raise ValueError(
                "Key-pair authentication requires cryptography library. "
                "It should be bundled with snowflake-connector-python."
            )

        passphrase = os.getenv("SNOWFLAKE_PRIVATE_KEY_PASSPHRASE")
        passphrase_bytes = passphrase.encode() if passphrase else None

        try:
            if key_path:
                with open(key_path, "rb") as f:
                    key_data = f.read()
            else:
                key_data = base64.b64decode(key_raw)

            private_key = serialization.load_pem_private_key(
                key_data, password=passphrase_bytes, backend=default_backend()
            )

            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )

            return "keypair", {"private_key": private_key_bytes}
        except Exception as e:
            raise ValueError(f"Failed to load private key: {e}")

    # Password authentication
    password = os.getenv("SNOWFLAKE_PASSWORD")
    if password:
        return "password", {"password": password}

    raise ValueError(
        "No authentication method configured. Set one of: "
        "SNOWFLAKE_PASSWORD, SNOWFLAKE_PRIVATE_KEY_PATH, "
        "SNOWFLAKE_PRIVATE_KEY_RAW, or SNOWFLAKE_AUTHENTICATOR"
    )


def build_connection_params(args: argparse.Namespace) -> Dict[str, Any]:
    """Build connection parameters from environment and CLI args."""
    # Check required environment variables
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    # Base connection params
    params: Dict[str, Any] = {
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "login_timeout": args.timeout,
        "network_timeout": args.timeout,
    }

    # Optional connection params (CLI args override env vars)
    if args.database or os.getenv("SNOWFLAKE_DATABASE"):
        params["database"] = args.database or os.getenv("SNOWFLAKE_DATABASE")

    if args.schema or os.getenv("SNOWFLAKE_SCHEMA"):
        params["schema"] = args.schema or os.getenv("SNOWFLAKE_SCHEMA")

    if args.warehouse or os.getenv("SNOWFLAKE_WAREHOUSE"):
        params["warehouse"] = args.warehouse or os.getenv("SNOWFLAKE_WAREHOUSE")

    if args.role or os.getenv("SNOWFLAKE_ROLE"):
        params["role"] = args.role or os.getenv("SNOWFLAKE_ROLE")

    # Authentication params
    auth_method, auth_params = detect_auth_method()
    params.update(auth_params)

    return params


def read_sql_file(file_path: str) -> str:
    """Read SQL from file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"SQL file not found: {file_path}")
    return path.read_text(encoding="utf-8")


def apply_limit(query: str, limit: int) -> str:
    """
    Apply LIMIT clause to query if not already present.
    Only applies to SELECT statements.
    """
    query_stripped = query.strip().rstrip(";")
    query_upper = query_stripped.upper()

    # Only apply to SELECT statements
    if not query_upper.startswith("SELECT"):
        return query

    # Check if LIMIT already exists (simple check)
    if re.search(r"\bLIMIT\s+\d+\s*$", query_upper):
        return query

    return f"{query_stripped} LIMIT {limit}"


def execute_query(
    conn: snowflake.connector.SnowflakeConnection,
    query: str,
    limit: Optional[int] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """
    Execute query and return results.

    Returns:
        {
            'columns': ['col1', 'col2', ...],
            'rows': [{'col1': val1, ...}, ...],
            'row_count': int,
            'query_id': str,
            'execution_time_ms': float
        }
    """
    # Apply limit if specified
    if limit is not None and limit > 0:
        query = apply_limit(query, limit)

    if verbose:
        print(f"Executing query: {query[:200]}...", file=sys.stderr)

    start_time = time.time()

    with conn.cursor(DictCursor) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        query_id = cursor.sfqid
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

    execution_time_ms = (time.time() - start_time) * 1000

    return {
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "query_id": query_id,
        "execution_time_ms": round(execution_time_ms, 2),
    }


def test_connection(
    conn: snowflake.connector.SnowflakeConnection,
) -> Dict[str, Any]:
    """Test connection with a simple query."""
    result = execute_query(conn, "SELECT CURRENT_TIMESTAMP() AS connected_at", limit=1)
    return {
        "status": "success",
        "message": "Connection successful",
        "connected_at": result["rows"][0]["CONNECTED_AT"] if result["rows"] else None,
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
    }


def format_json(result: Dict[str, Any]) -> str:
    """Format result as JSON."""
    output = {
        "status": "success",
        "query_id": result["query_id"],
        "execution_time_ms": result["execution_time_ms"],
        "row_count": result["row_count"],
        "columns": result["columns"],
        "rows": result["rows"],
    }
    return json.dumps(output, indent=2, default=json_serializer)


def format_table(result: Dict[str, Any]) -> str:
    """Format result as ASCII table."""
    if not HAS_TABULATE:
        raise ImportError(
            "Table format requires tabulate. "
            "Run with: uvx --with snowflake-connector-python --with tabulate python query.py ..."
        )

    if not result["rows"]:
        return "(No rows returned)"

    # Convert list of dicts to list of lists for tabulate
    headers = result["columns"]
    rows = [[row.get(col) for col in headers] for row in result["rows"]]

    table = tabulate(rows, headers=headers, tablefmt="grid")

    # Add metadata footer
    footer = f"\n({result['row_count']} rows, {result['execution_time_ms']}ms)"
    return table + footer


def format_csv(result: Dict[str, Any]) -> str:
    """Format result as CSV."""
    if not result["rows"]:
        return ""

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=result["columns"])
    writer.writeheader()
    writer.writerows(result["rows"])
    return output.getvalue()


def output_result(
    result: Dict[str, Any],
    format_type: str,
    output_path: Optional[str] = None,
) -> None:
    """Output result in specified format."""
    formatters = {
        "json": format_json,
        "table": format_table,
        "csv": format_csv,
    }

    formatter = formatters.get(format_type)
    if not formatter:
        raise ValueError(f"Unknown format: {format_type}")

    formatted = formatter(result)

    if output_path:
        Path(output_path).write_text(formatted, encoding="utf-8")
        # Print confirmation to stderr
        print(
            json.dumps(
                {
                    "status": "success",
                    "message": f"Output written to {output_path}",
                    "row_count": result["row_count"],
                    "format": format_type,
                }
            ),
            file=sys.stderr,
        )
    else:
        print(formatted)


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(
        description="Execute SQL queries against Snowflake",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --query "SELECT * FROM my_table"
  %(prog)s --file query.sql --format table
  %(prog)s -q "SHOW TABLES" --format csv -o tables.csv
  %(prog)s --dry-run
        """,
    )

    # Query input (mutually exclusive group)
    query_group = parser.add_mutually_exclusive_group()
    query_group.add_argument(
        "-q", "--query", type=str, help="SQL query string"
    )
    query_group.add_argument(
        "-f", "--file", type=str, help="SQL file path"
    )

    # Output options
    parser.add_argument(
        "--format",
        type=str,
        choices=["json", "table", "csv"],
        default="json",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "-o", "--output", type=str, help="Output file path (default: stdout)"
    )

    # Result control
    parser.add_argument(
        "-l",
        "--limit",
        type=int,
        default=DEFAULT_LIMIT,
        help=f"Row limit (default: {DEFAULT_LIMIT})",
    )
    parser.add_argument(
        "--no-limit",
        action="store_true",
        help="Disable row limit (fetch all rows)",
    )

    # Connection overrides
    parser.add_argument("--database", type=str, help="Override database")
    parser.add_argument("--schema", type=str, help="Override schema")
    parser.add_argument("--warehouse", type=str, help="Override warehouse")
    parser.add_argument("--role", type=str, help="Override role")

    # Other options
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"Query timeout in seconds (default: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Test connection only (don't execute query)",
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Verbose output"
    )

    return parser


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Validate: need query or file (unless dry-run)
    if not args.dry_run and not args.query and not args.file:
        output_error("MISSING_QUERY", ERROR_CODES["MISSING_QUERY"])
        return 1

    try:
        # Build connection parameters
        conn_params = build_connection_params(args)

        if args.verbose:
            # Mask sensitive info
            safe_params = {
                k: "***" if k in ("password", "private_key", "token") else v
                for k, v in conn_params.items()
            }
            print(f"Connection params: {safe_params}", file=sys.stderr)

    except ValueError as e:
        if "Missing required environment" in str(e):
            output_error("MISSING_ENV_VAR", str(e))
            return 1
        elif "authentication" in str(e).lower():
            output_error("NO_AUTH_METHOD", str(e))
            return 2
        elif "private key" in str(e).lower():
            output_error("INVALID_PRIVATE_KEY", str(e))
            return 2
        else:
            output_error("INVALID_OPTION", str(e))
            return 1

    # Connect to Snowflake
    try:
        if args.verbose:
            print("Connecting to Snowflake...", file=sys.stderr)

        conn = snowflake.connector.connect(**conn_params)

    except DatabaseError as e:
        error_msg = str(e)
        if "auth" in error_msg.lower() or "password" in error_msg.lower():
            output_error("AUTH_FAILED", error_msg)
            return 2
        else:
            output_error("CONNECTION_FAILED", error_msg)
            return 3
    except Exception as e:
        output_error("CONNECTION_FAILED", str(e))
        return 3

    try:
        # Dry run: just test connection
        if args.dry_run:
            result = test_connection(conn)
            print(json.dumps(result, indent=2, default=json_serializer))
            return 0

        # Get query
        if args.file:
            try:
                query = read_sql_file(args.file)
            except FileNotFoundError as e:
                output_error("FILE_NOT_FOUND", str(e))
                return 1
        else:
            query = args.query

        # Determine limit
        limit = None if args.no_limit else args.limit

        # Execute query
        result = execute_query(conn, query, limit=limit, verbose=args.verbose)

        # Output result
        try:
            output_result(result, args.format, args.output)
        except ImportError as e:
            output_error("FORMAT_NOT_SUPPORTED", str(e))
            return 5
        except IOError as e:
            output_error("OUTPUT_WRITE_FAILED", str(e))
            return 5

        return 0

    except ProgrammingError as e:
        output_error("QUERY_ERROR", str(e), {"query_id": getattr(e, "sfqid", None)})
        return 4
    except OperationalError as e:
        output_error("QUERY_ERROR", str(e))
        return 4
    except Exception as e:
        output_error("QUERY_ERROR", str(e))
        return 4
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
