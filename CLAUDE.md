# Claude Haggler Skills - Development Guide

This is a Claude Code skills marketplace repository. Follow these guidelines when contributing.

## Directory Structure

```
claude-haggler-skills/
├── .claude-plugin/
│   └── marketplace.json    # Plugin registry (defines available plugins)
├── CLAUDE.md               # This file (development guide)
├── README.md               # User-facing documentation
├── LICENSE                 # Repository license
└── skills/
    └── <skill-name>/       # One folder per skill
        ├── SKILL.md        # Skill definition (required)
        ├── LICENSE.txt     # Skill license (optional)
        └── scripts/        # Implementation scripts (optional)
```

## Adding a New Skill

### 1. Create Skill Directory

```bash
mkdir -p skills/<skill-name>/scripts
```

### 2. Create SKILL.md

Every skill requires a `SKILL.md` file with YAML frontmatter:

```markdown
---
name: <skill-name>
description: "Brief description of what this skill does and when to use it."
license: MIT
---

# Skill Title

## Overview
[Detailed explanation of the skill]

## Usage
[How to invoke and use the skill]

## Examples
[Concrete examples]
```

**Required frontmatter fields:**
- `name`: Lowercase, hyphens for spaces (e.g., `md2ipynb`)
- `description`: Complete description including trigger conditions

**Optional frontmatter fields:**
- `license`: License type or reference to LICENSE.txt

### 3. Add Implementation Scripts (Optional)

Place any supporting scripts in `scripts/` subdirectory:

```
skills/<skill-name>/
└── scripts/
    └── main.py
```

### 4. Register in marketplace.json

Add the skill path to the appropriate plugin in `.claude-plugin/marketplace.json`:

```json
{
  "plugins": [
    {
      "name": "converter-skills",
      "skills": [
        "./skills/existing-skill",
        "./skills/<new-skill>"
      ]
    }
  ]
}
```

Or create a new plugin group if appropriate.

## Testing Skills

1. Install the marketplace locally:
   ```
   /plugin marketplace add /path/to/claude-haggler-skills
   ```

2. Install the plugin:
   ```
   /plugin install converter-skills@claude-haggler-skills
   ```

3. Test the skill by invoking it in a conversation

## Coding Standards

- Write all documentation in English
- Use clear, descriptive names
- Include error handling in scripts
- Add usage examples in SKILL.md
- Keep skills focused on a single purpose

## Commit Messages

Use conventional commits:
- `feat: add new skill <name>`
- `fix: correct behavior in <skill>`
- `docs: update README`
