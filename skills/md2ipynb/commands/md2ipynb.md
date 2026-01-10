---
description: Convert markdown file to Jupyter notebook (.ipynb)
argument-hint: <input.md> [output.ipynb]
allowed-tools: Bash(uvx:*)
---

# Markdown to Jupyter Notebook Conversion

Convert the specified markdown file to a Jupyter notebook.

## Arguments

- `$1`: Input markdown file path (required)
- `$2`: Output notebook file path (optional, defaults to input filename with .ipynb extension)

## Conversion Rules

- Split by `---` horizontal rules into separate cells
- Extract fenced code blocks (`python`, `sql`) as code cells
- Automatically remove YAML front matter

## Execution

Run the conversion script using uvx:

```bash
uvx --with nbformat python skills/md2ipynb/scripts/convert.py "$1" "${2:-${1%.md}.ipynb}"
```

If `$2` is not provided, derive output filename from input by replacing `.md` with `.ipynb`.
