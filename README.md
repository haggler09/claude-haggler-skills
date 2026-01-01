# Claude Haggler Skills

A Claude Code skills marketplace providing custom skills for document processing and conversion.

## Installation

### 1. Add the Marketplace

```
/plugin marketplace add haggler09/claude-haggler-skills
```

### 2. Install a Plugin

```
/plugin install converter-skills@claude-haggler-skills
```

## Available Plugins

### converter-skills

Collection of document conversion skills.

| Skill | Description |
|-------|-------------|
| `md2ipynb` | Convert markdown files to Jupyter notebooks (.ipynb) |

### data-skills

Collection of data access and query skills.

| Skill | Description |
|-------|-------------|
| `snowflake-query` | Execute SQL queries against Snowflake data warehouse |

## Skills Reference

### md2ipynb

Converts markdown files to Jupyter notebooks with intelligent cell splitting:

- Splits by `---` horizontal rules into separate cells
- Extracts fenced code blocks (`python`, `sql`) as code cells
- Automatically removes YAML front matter

**Usage:**
```
/converter-skills:md2ipynb
```

**CLI:**
```bash
uvx --with nbformat python scripts/convert.py input.md output.ipynb
```

### snowflake-query

Execute SQL queries against Snowflake with support for multiple authentication methods:

- Password, key-pair, and SSO/OAuth authentication
- Output formats: JSON, table, CSV
- Connection parameter overrides (database, schema, warehouse, role)

**Usage:**
```
/data-skills:snowflake-query
```

**CLI:**
```bash
uvx --with snowflake-connector-python python scripts/query.py --query "SELECT 1"
```

## Contributing

See [CLAUDE.md](CLAUDE.md) for development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
