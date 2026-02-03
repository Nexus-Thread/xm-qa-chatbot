# ADR-001: Hexagonal Architecture

## Context
The system needs swappable adapters for storage, LLM providers, and user interfaces.

## Decision
Adopt a hexagonal architecture with explicit ports and adapters.

## Consequences
We introduce more structure and interfaces, but gain clearer boundaries and replaceable
infrastructure components.

## Alternatives
Layered architecture without ports and adapters.