# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability in this project, please report it responsibly.

### How to Report

1. **Do not** open a public issue
2. Email the maintainer directly or use GitHub's private vulnerability reporting feature
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 1 week
- **Resolution Timeline**: Depends on severity
  - Critical: As soon as possible
  - High: Within 2 weeks
  - Medium/Low: Next regular release

### Scope

This policy applies to:
- Skill implementations in `skills/`
- Configuration files
- Build and development scripts

### Out of Scope

- Issues in Claude Code itself (report to Anthropic)
- Third-party dependencies (report to respective maintainers)

## Security Best Practices for Contributors

When contributing skills:
- Never include credentials or secrets
- Validate all user inputs
- Use secure coding practices
- Document any external dependencies
