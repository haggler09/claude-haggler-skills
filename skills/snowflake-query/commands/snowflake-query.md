---
description: Execute SQL query against Snowflake data warehouse
argument-hint: <query or -f file.sql> [options]
allowed-tools: Bash(uvx:*)
---

# Snowflake Query Execution

Execute SQL queries against Snowflake using the Python connector.

## Arguments

- `$ARGUMENTS`: SQL query string or options including `-f <file.sql>`

## Prerequisites

Ensure required environment variables are set:
- `SNOWFLAKE_ACCOUNT`: Account identifier
- `SNOWFLAKE_USER`: Username
- Authentication: `SNOWFLAKE_PASSWORD`, `SNOWFLAKE_PRIVATE_KEY_PATH`, or `SNOWFLAKE_AUTHENTICATOR`

## Examples

```bash
# Inline query
/snowflake-query -q "SELECT * FROM my_table LIMIT 10"

# From SQL file
/snowflake-query -f query.sql

# With table format output
/snowflake-query -q "SHOW TABLES" --format table

# Export to CSV
/snowflake-query -q "SELECT * FROM users" --format csv -o users.csv

# Test connection
/snowflake-query --dry-run
```

## Execution

Run the query script using uvx:

```bash
# For JSON/CSV output
uvx --with snowflake-connector-python python skills/snowflake-query/scripts/query.py $ARGUMENTS

# For table output (include tabulate)
uvx --with snowflake-connector-python --with tabulate python skills/snowflake-query/scripts/query.py $ARGUMENTS
```

Check if `--format table` is in arguments to include tabulate dependency.
