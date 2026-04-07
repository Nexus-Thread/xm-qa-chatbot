---
name: format-python-code
description: Formats Python code using ruff and applies safe auto-fixes.
---

# Skill: Format Python Code

Use this skill to format Python code and apply safe auto-fixes using `ruff`.

## Prerequisites

- `uv` is installed and configured for the project.
- `ruff` is installed as a development dependency and configured in `pyproject.toml`.

## Steps

### 1. Apply auto-fixes and format

```bash
uv run ruff check . --fix
uv run ruff format .
```

These commands will automatically reformat Python code and apply any safe linting auto-fixes.

## When formatting fails

- If `ruff format .` produces unexpected changes, verify that the project's `pyproject.toml` ruff configuration is correct before overriding the formatter.
- Unfixable lint violations reported by `ruff check . --fix` will be caught and addressed during the `lint-python-code` step.
