# Workflow: update repo navigation

Use this workflow when adapting the reusable hexagonal Python rules to a specific project.

## Goal
Produce a short, project-specific navigation guide outside `.clinerules/` so contributors can quickly find package roots, entry points, adapters, and tests.

When documenting reusable navigation workflows, prefer cross-platform examples based on IDE search or `rg`/`rg --files`.

## Recommended output location
- `docs/repo-navigation.md`
- or another discoverable project-owned path near the main developer docs

## Steps
1. Identify the package root (`src/<package_name>/` or the top-level package directory).
2. Locate entry points and composition-root/bootstrap files (`__main__.py`, `cli.py`, ASGI/WSGI app factories, worker startup modules, etc.).
3. Map the hexagonal layers:
   - `domain/`
   - `application/`
   - `adapters/input/`
   - `adapters/output/`
   - shared infrastructure or bootstrap modules, if present
4. Map the test layout (`tests/unit/`, `tests/integration/`, `tests/e2e/`, shared fixtures, contract tests).
5. Record the most useful project-specific search commands for ports, adapters, entry points, and tests.
6. Save the navigation guide outside `.clinerules/` and update it whenever the structure changes significantly.

## Suggested template
```md
# Project navigation

## Package roots
- `src/myproject/`

## Entry points / composition root
- `src/myproject/cli.py`
- `src/myproject/bootstrap.py`

## Domain
- `src/myproject/domain/`

## Application
- `src/myproject/application/`

## Adapters
- Input: `src/myproject/adapters/input/`
- Output: `src/myproject/adapters/output/`

## Tests
- Unit: `tests/unit/`
- Integration: `tests/integration/`
- E2E: `tests/e2e/`

## Useful search commands
- `rg "Protocol|ABC|abstractmethod" src/myproject/application/ports/`
- `rg --files src/myproject/adapters/ | rg "(^|/)(adapter\.py|.*_adapter\.py)$"`
- `rg --files -g "pyproject.toml"`
- `rg --files src/myproject/ | rg "(^|/)(__main__|cli)\.py$"`
```
