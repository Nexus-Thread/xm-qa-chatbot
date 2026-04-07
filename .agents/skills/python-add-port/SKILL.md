---
name: python-add-port
description: Add a technology-agnostic application port interface to a Python hexagonal project for a new use case or dependency.
---

# Add a Port

Use this skill to add a port interface to a Python hexagonal project.

A port defines an application-layer boundary. It describes either how the
outside world uses the application or what the application needs from external
systems. A port is not an adapter and must remain technology-agnostic.

This skill owns the detailed procedure for defining new application ports.
Keep feature orchestration and adapter implementation in related skills.

## When to use this skill

Use this skill when you need to:

- expose a new use case through an input port
- define a new dependency the application needs through an output port
- extract an application-facing interface so adapters depend on an application
  contract rather than concrete implementation details

## Prerequisites

- The project follows a hexagonal structure under `src/<app_name>/`.
- You understand the use case or dependency the port represents.
- Any command, query, or result DTOs used by the port already exist or are part
  of the same change.

## Port types

### Input port

An input port defines how the outside world invokes an application use case.
It is called by an input adapter and implemented by an application service.

Examples:

- `CreateOrderPort`
- `RegisterUserPort`
- `GenerateReportPort`

### Output port

An output port defines a dependency the application needs from external
infrastructure. It is declared by the application and implemented by an output
adapter.

Examples:

- `OrderRepositoryPort`
- `EmailSenderPort`
- `PaymentGatewayPort`

## Steps

### 1. Choose the file and name

Create the interface under:

```
src/<app_name>/application/ports/
```

Use a focused file name that matches the responsibility, for example:

- `<use_case_name>_port.py`
- `<dependency_name>_port.py`

Name both the file and the class by business capability or dependency, not by
technology.

Good: `CreateInvoicePort`, `CustomerRepositoryPort`

Avoid: `FastAPIPort`, `PostgresPort`, `S3AdapterPort`

### 2. Define the interface

Use `Protocol` by default for lightweight structural typing. Use `ABC` only
when you need shared abstract behavior or stricter inheritance semantics.

Example:

```python
from typing import Protocol

from <app_name>.application.commands.create_invoice import CreateInvoiceCommand
from <app_name>.application.results.create_invoice import CreateInvoiceResult


class CreateInvoicePort(Protocol):
    def execute(self, command: CreateInvoiceCommand) -> CreateInvoiceResult:
        ...
```

For output ports, follow the same pattern using domain objects or application
DTOs in the signature.

### 3. Keep the port clean

- Keep ports in the application layer.
- Do not import from `adapters/` or infrastructure libraries.
- Do not embed framework request or response types in port method signatures.
- Prefer domain objects and application DTOs in method signatures.
- Keep each port narrowly focused on one use case or one dependency role.
- Name methods by business intent, not transport or storage mechanics.

For input ports, a single `execute(...)` method is often enough.

For output ports, define only the operations the application needs. Do not
mirror a full ORM, SDK, or driver API.

### 4. Wire dependencies in the right direction

The arrows below show call/invocation flow (who calls whom), not import dependency direction. For dependency direction rules, see `03-architecture-guardrails.md`.

```text
input adapters -> input ports -> application service
application service -> output ports -> output adapters
```

In practice:

- input adapters depend on input port contracts
- application services implement input ports
- application services depend on output port contracts
- output adapters implement output ports

Never let a port import an adapter or mention a specific framework.

### 5. Test appropriately

Ports are interfaces, so they usually need little or no direct testing.

Test surrounding behavior instead:

- unit test that the application service honors the input port contract
- unit test that application services call output ports as expected
- test adapter implementations separately in adapter-focused tests

If the project uses runtime-checkable protocols or shared contract fixtures, add
small targeted tests only when they provide clear value.

### 6. Review related changes

When adding a new port, check whether the same change needs:

- a new application service implementing the input port
- a new output adapter implementing the output port
- new command, query, or result DTOs
- dependency injection or composition-root wiring updates

If a required adapter does not exist yet, use `python-add-adapter` for that
follow-up work instead of embedding adapter logic into the port.

If the overall change is a complete end-to-end use case spanning domain,
application service, and tests, use `add-hexagonal-feature` as the primary
feature workflow and use this skill only for the port-definition part.
