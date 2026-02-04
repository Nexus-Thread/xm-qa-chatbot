# ADR-004: Storage Strategy and Migrations

## Context
Submissions must be persisted for dashboard aggregation and auditing. We also need a migration path for schema changes over time.

## Decision
Use a SQLite-backed adapter (`SQLiteAdapter`) implementing `StoragePort`, with Alembic-managed migrations. The initial schema is defined in the existing migration under `migrations/versions/`.

## Consequences
Local development remains lightweight while preserving migration discipline. Schema changes require adding Alembic revisions.

## Alternatives
- Use a document store for submissions
- Skip migrations and rely on ad-hoc schema updates
