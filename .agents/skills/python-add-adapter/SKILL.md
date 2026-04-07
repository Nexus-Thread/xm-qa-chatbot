---
name: python-add-adapter
description: Add an input or output adapter to a Python hexagonal project while keeping business logic in the application layer.
---

# Add an Adapter

Add an input or output adapter to a Python hexagonal project while keeping business logic in the application layer.

This skill owns adapter implementation. If the required application boundary
does not exist yet, define the port first with `python-add-port`.

## Prerequisites

- The relevant port interface exists in `src/<app_name>/application/ports/`.
- The adapter technology has been chosen and any required library is installed (for example with `uv add <library>`).

If the port does not exist yet, use `python-add-port` before implementing the
adapter.

## Input adapter

An input adapter receives external input and calls the application through an input port or service entry point.

### 1. Create the module

```
src/<app_name>/adapters/input/<adapter_name>/
    __init__.py
    adapter.py
```

Keep `__init__.py` lightweight. Re-export the public symbol only when you want a stable package-level API, and declare `__all__` when it adds clarity:

```python
from .adapter import router

__all__ = ["router"]
```

### 2. Implement

- Accept external input and map it to an application command or query DTO.
- Call the application through its input port or service entry point.
- Map the result or exception back to the external format.
- Map domain exceptions to adapter-level error responses.
- Do not import from `domain/` directly.
- Keep all business logic in the application service.

### 3. Test

Place tests under `tests/integration/<adapter_name>/`. Test through the framework test client or transport boundary, injecting a fake or stubbed application service to keep tests focused on adapter behavior.

Add unit tests only if the adapter contains meaningful mapping or serialization helpers that warrant direct, framework-free verification.

## Output adapter

An output adapter implements a port interface and talks to external infrastructure.

### 1. Create the module

```
src/<app_name>/adapters/output/<adapter_name>/
    __init__.py
    adapter.py
```

Keep `__init__.py` lightweight. Re-export the public symbol only when you want a stable package-level API, and declare `__all__` when it adds clarity:

```python
from .adapter import <AdapterName>

__all__ = ["<AdapterName>"]
```

### 2. Implement

- Implement all port interface methods.
- Map infrastructure types to domain objects inside the adapter. Do not expose infrastructure types beyond the adapter boundary.
- Raise domain exceptions, not infrastructure exceptions.
- Keep framework clients, ORM models, serializers, and transport-specific configuration inside the adapter package.

### 3. Test

Write unit tests using fakes, stubs, or mocks around the infrastructure boundary. Follow with integration tests against the real infrastructure when adapter behavior depends on actual driver, network, or persistence integration.
