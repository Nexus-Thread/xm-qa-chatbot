---
name: add-hexagonal-feature
description: Implement a new feature or use case in a Python hexagonal project, including domain modeling, ports, application service, and tests.
---

# Skill: Add a Hexagonal Feature

Use this skill to implement a new feature, use case, or business capability in
a Python hexagonal project.

This skill focuses on the application and domain changes needed to add a use
case cleanly. It owns feature-level orchestration across domain,
application, and tests. When the change requires a new port or adapter, use
the specialized skill for that procedure instead of duplicating it here.

## Prerequisites

- The project already has the standard hexagonal `src/` layout.
- The feature is clear enough that you understand its inputs, outputs, and core
  business rules.

## Steps

### 1. Name the use case

Choose a clear verb-noun name for the use case, for example `PlaceOrder`,
`RegisterUser`, or `SendNotification`. Use that name consistently for the
related files and classes.

### 2. Model the domain if needed

Create or update files under `src/<app_name>/domain/`:

- **Entity** — an object with identity that changes over time.
- **Value object** — an immutable descriptor (e.g. `EmailAddress`, `Money`).
- **Domain event** — something that happened (e.g. `OrderPlaced`).

Rules:

- Domain objects must be pure Python with no framework imports or I/O.
- Use `@dataclass(frozen=True)` for value objects.
- Raise domain-specific exceptions, not HTTP or database errors.

```python
# src/<app_name>/domain/<entity>.py
from dataclasses import dataclass

@dataclass
class <Entity>:
    id: str
```

### 3. Define or confirm the required ports

Identify the application boundaries the feature needs:

- an input port when an external caller invokes a new use case
- one or more output ports when the application needs infrastructure
  dependencies such as repositories, publishers, or gateways

If a required port does not exist yet, use `python-add-port` for the detailed
procedure. In this skill, keep the focus on deciding which boundaries the
feature needs and making sure the application service depends only on those
port contracts.

### 4. Implement the application service

Create the use case implementation under `src/<app_name>/application/`:

```python
class <UseCaseName>:
    def __init__(self, repository: <EntityRepositoryPort>) -> None:
        self._repository = repository

    def execute(self, command: <Command>) -> <Result>:
        ...
```

Rules:

- The application service depends only on domain objects and port interfaces.
- It must not import from `adapters/`.
- It must not perform I/O directly, including `open()`, HTTP calls, or database
  access.
- If the feature needs a new adapter implementation for an existing or new
  port, use `python-add-adapter` for that procedure.

### 5. Write unit tests

Create tests under `tests/unit/`:

```python
from unittest.mock import MagicMock

def test_<use_case_name>_happy_path() -> None:
    repo = MagicMock()
    use_case = <UseCaseName>(repository=repo)
    use_case.execute(<Command>(...))
    repo.save.assert_called_once()
```

TDD is encouraged when it fits the change. Writing tests before the
implementation is fine and often preferable.

- Use `MagicMock` or a hand-written fake for outbound ports, never real
  infrastructure.
- Cover the happy path and at least one failure or edge case.

## Dependency direction reminder

The canonical dependency rules are in `03-architecture-guardrails.md`. This diagram is a quick reference only.

```
adapters/input   →  application  →  domain
adapters/output  →  (implements application/ports)
```

Never let an arrow point in the opposite direction.
