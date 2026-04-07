# Tooling and CI conventions

This ruleset uses an opinionated toolchain:
- `uv` for dependency management, environment management, and command execution
- `ruff` for formatting, linting, and import cleanup
- `mypy` for type checking
- `pytest` for tests

Run project tooling through `uv run ...` and keep tool configuration in `pyproject.toml`.

## Local quality gate
Use the `run-local-quality-gate` skill to execute the full local quality gate workflow.

When validating changes, use this order:

1. **Run Local Quality Gate**
   - Use the `run-local-quality-gate` skill.

2. **Optional project gates**
   - Coverage thresholds
   - Security/static-analysis checks
   - Dependency/license audits
   - Docs build or examples smoke tests

## Expectations
- Generated code **must** satisfy `uv run ruff check .`, `uv run mypy .`, and `uv run pytest` with no unapproved failures.
- Code **must** be formatted with `uv run ruff format .`.
- If behavior changes, you **must** add or adjust tests and run the relevant impacted suites.
- Do not disable lint rules unless explicitly requested; prefer refactoring.
- CI failures must be fixed at the root cause.

## Usage clarifications
- Run the full quality gate before handoff, even if only a single file changed.
- If a change impacts only a subset of tests, run that subset first,
  but still complete `uv run pytest` before handoff.
- In monorepos, run the same `uv run ...` gates from the affected package/service root plus any impacted shared gates.
- Pre-commit hooks provide helpful fast feedback, but they do **not** replace the full local quality gate.
- For flaky or slow tests, document the reason and mitigation in the handoff notes.
- If any step fails, address the underlying issue rather than proceeding to the next step.
- Do not bypass `pyproject.toml`-backed tool configuration with ad hoc flags in the final validation run.

## Reproducibility and dependency hygiene
- Dependency changes **must** update `pyproject.toml` and `uv.lock` together.
- CI should validate in a clean environment created with `uv sync --frozen --all-groups`.
- Keep the supported Python version(s) documented in `pyproject.toml` and CI so local and remote validation target the same baseline.

## Architecture validation
- If a change crosses layers, include tests that prove boundary adherence (ports invoked, adapters wired).
- Document any intentional rule exceptions in the PR description and handoff notes.
