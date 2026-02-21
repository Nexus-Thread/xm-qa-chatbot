# ADR-004: Storage Strategy and Migrations

## Context
Submission data is required for monthly reporting, dashboard generation, and historical auditing. The project needs:
- a local-first persistence option for low-friction development,
- stable schema evolution over time,
- explicit boundaries between domain/application logic and persistence concerns.

Without migration discipline, schema drift would become ad-hoc and risky as data shape evolves.

## Decision
Use a SQLite-backed storage adapter (`SQLiteAdapter`) behind `StoragePort`, with Alembic-managed schema migrations.

Persistence I/O and ORM mapping remain in adapter/infrastructure code, while application use cases interact only through storage port contracts. Schema changes are introduced through explicit migration revisions in `migrations/versions/`.

## Consequences
- Positive:
  - Lightweight local setup and reproducible developer environments.
  - Clear migration history for schema evolution and rollback planning.
  - Storage concerns remain isolated behind the output port boundary.
- Trade-offs:
  - SQLite has different concurrency and operational characteristics than managed server databases.
  - Adapter/migration maintenance overhead is required even for small schema changes.
  - Cross-environment behavior (local vs production-grade DBs) may diverge in future.
- Follow-up implications:
  - Future move to another database should happen via a new adapter while preserving `StoragePort`.
  - Every schema change must ship with an Alembic migration and corresponding tests.

## Alternatives
- Persist submissions in a document store.
- Skip migration tooling and perform manual/ad-hoc schema changes.
- Introduce a heavier managed SQL database immediately instead of starting with SQLite.
