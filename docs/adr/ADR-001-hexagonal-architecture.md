# ADR-001: Hexagonal Architecture

## Context
The chatbot integrates multiple external concerns that are expected to evolve independently over time:
- input surfaces (currently Gradio, potentially CLI/API later),
- persistence strategies (currently SQLite, possible managed database later),
- LLM providers and transport policies,
- dashboard output targets (HTML and Confluence-oriented artifacts).

Without strict boundaries, infrastructure concerns can leak into business logic and make testing slow, brittle, and tightly coupled to specific frameworks or SDKs. The project also needs predictable navigation and clear ownership of responsibilities across modules.

## Decision
Adopt hexagonal architecture as the baseline system design, with explicit application-layer ports and adapter-layer implementations.

The repository is organized around domain, application, and adapters, with dependency direction pointing inward toward the domain/application core. Use cases orchestrate business flows through ports, while adapters handle translation, I/O, and framework integration.

This decision is a hard architectural guardrail for feature work and refactoring.

## Consequences
- Positive:
  - Business logic remains testable without real network/database dependencies.
  - Infrastructure can be replaced incrementally (for example, different LLM/persistence adapters) without rewriting core use cases.
  - Adapter contracts clarify responsibilities and reduce cross-layer coupling.
- Trade-offs:
  - More interfaces, DTO mapping, and wiring code than a monolithic layered module.
  - Developers must maintain boundary discipline in imports and module placement.
  - Some changes require edits in more than one layer (port + adapter + wiring).
- Follow-up implications:
  - New external integrations must be introduced as adapters behind ports.
  - Reviews should include architecture-boundary checks as a first-class criterion.

## Alternatives
- Conventional layered architecture with direct infrastructure calls from application services.
- Framework-centric architecture where transport/storage models are shared across business logic.
- A single-module design optimized for short-term speed at the cost of long-term replaceability and test isolation.
