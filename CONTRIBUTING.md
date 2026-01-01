# Contributing to Claude Haggler Skills

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Bugs

1. Check existing issues to avoid duplicates
2. Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md)
3. Include steps to reproduce, expected vs actual behavior

### Suggesting Features

1. Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md)
2. Describe the use case and proposed solution
3. Be open to discussion and feedback

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch from `master`
3. Make your changes following the guidelines below
4. Submit a PR using the [Pull Request template](.github/PULL_REQUEST_TEMPLATE.md)

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-haggler-skills.git
   cd claude-haggler-skills
   ```

2. Install the marketplace locally for testing:
   ```
   /plugin marketplace add /path/to/claude-haggler-skills
   /plugin install converter-skills@claude-haggler-skills
   ```

3. Test your skill in a conversation

## Adding a New Skill

See [CLAUDE.md](CLAUDE.md) for detailed instructions on:
- Directory structure
- SKILL.md format
- Required frontmatter fields
- Implementation scripts

### Quick Checklist

- [ ] Create `skills/<skill-name>/SKILL.md` with proper frontmatter
- [ ] Add skill path to `.claude-plugin/marketplace.json`
- [ ] Include usage examples in SKILL.md
- [ ] Add LICENSE.txt if different from repository license
- [ ] Test the skill locally

## Code Style

- Write all documentation in English
- Use clear, descriptive names
- Include error handling in scripts
- Keep skills focused on a single purpose
- Follow existing patterns in the codebase

## Commit Messages

Use conventional commit format:
- `feat: add new skill <name>`
- `fix: correct behavior in <skill>`
- `docs: update README`
- `chore: update dependencies`

## Questions?

Open an issue for any questions or clarifications.
