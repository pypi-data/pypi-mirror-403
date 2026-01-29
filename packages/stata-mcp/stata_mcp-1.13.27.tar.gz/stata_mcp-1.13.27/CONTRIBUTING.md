# CONTRIBUTING
Thank you for your interest in contributing to this project! We welcome contributions from everyone. Please follow the guidelines below to ensure a smooth process.

## Git Commit Standards

We follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification for all commit messages. This creates a structured commit history that is both human and machine readable.

### Basic Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Commit Types

| Type | Description | SemVer Impact |
|------|-------------|---------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation changes | NONE |
| `style` | Code formatting (no functional changes) | NONE |
| `refactor` | Code refactoring | NONE |
| `perf` | Performance improvements | NONE |
| `test` | Testing related | NONE |
| `chore` | Build tools, auxiliary tools | NONE |
| `ci` | CI/CD configuration | NONE |
| `build` | Build system changes | NONE |
| `revert` | Revert a commit | NONE |

### Breaking Changes

Breaking changes MUST be indicated in one of two ways:

1. **Using `!` before the colon:**
   ```
   feat!: send an email to customer when product is shipped
   feat(api)!: remove deprecated endpoints
   ```

2. **Using BREAKING CHANGE footer:**
   ```
   feat: allow provided config object to extend other configs

   BREAKING CHANGE: `extends` key in config file is now used for extending other config files
   ```

Any commit with a breaking change correlates with a **MAJOR** version bump.

### Examples

**Simple commit:**
```bash
feat: add user avatar upload functionality
```

**With scope:**
```bash
feat(auth): add two-factor authentication
```

**With body and footer:**
```bash
fix: prevent racing of requests

Introduce a request id and a reference to latest request. Dismiss
incoming responses other than from latest request.

Fixes #123
```

**Breaking change:**
```bash
feat(api): update user API response format

BREAKING CHANGE:
User API response format has been updated:
- Removed `user_name` field
- Added `username` and `display_name` fields
```

### Using Claude Code for Commits

If you are not comfortable with git, you can ask Claude Code to help you commit changes. For example:
```bash
# In Claude Code, you can say:
> help me commit my change to github

# Or manually stage files and let Claude generate the message:
!git add <the_files_you_want_to_commit>
> help me commit the message to github

# Always review the commit before pushing
git push
```

**Important:** Always review the generated commit message for accuracy before pushing, as AI tools may sometimes make mistakes.

## Legal Notice

By contributing to this project, you agree to the terms of the [Contributor License Agreement](source/docs/Rights/CLA.md). If you do not have the rights to submit the code, please do not contribute.
