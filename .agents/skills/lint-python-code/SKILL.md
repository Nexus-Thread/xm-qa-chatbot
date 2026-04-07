---
name: lint-python-code
description: Lints Python code using ruff and mypy for type checking.
---

# Skill: Lint Python Code

Use this skill to lint Python code using `ruff` and perform type checking with `mypy`.

## Prerequisites

- `uv` is installed and configured for the project.
- `ruff` and `mypy` are installed as development dependencies and configured in `pyproject.toml`.

## Steps

### 1. Run ruff linting

```bash
uv run ruff check .
```

This command checks for linting errors without applying auto-fixes.

### 2. Run mypy type checking

```bash
uv run mypy .
```

This command performs static type checking on the Python codebase.

## When linting or type checking fails

- Read the `ruff check` output carefully. Each violation includes a rule code, file path, and line number. Fix the underlying code rather than adding `# noqa` comments unless the suppression is explicitly justified.
- Do not disable lint rules to silence violations. Prefer refactoring the code to satisfy the rule.
- Read `mypy` errors and fix the type annotations or logic that caused them. Use `# type: ignore[<code>]` only at narrowly scoped boundaries to genuinely untyped third-party code, and document the reason.
- If a `mypy` error reflects a genuine design issue (wrong return type, missing protocol method), fix the design rather than suppressing the error.
- After fixes, re-run both commands to confirm the codebase is clean before proceeding.
