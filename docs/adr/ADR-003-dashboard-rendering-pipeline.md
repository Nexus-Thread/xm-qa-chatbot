# ADR-003: Dashboard Rendering Pipeline

## Context
The project needs dashboard outputs that are easy to review, share, and regenerate from persisted submission data. Consumers currently need:
- browser-friendly static HTML for local inspection,
- Confluence-friendly HTML artifacts for manual publishing workflows.

Rendering logic must stay deterministic and testable, and should not leak template/output concerns into the domain or application core.

## Decision
Keep dashboard rendering behind `DashboardPort` and use a dual-output adapter composition:
- `GetDashboardDataUseCase` and `GenerateMonthlyReportUseCase` provide application-layer data payloads,
- `HtmlDashboardAdapter` renders browser-ready static pages,
- `ConfluenceDashboardAdapter` renders Confluence-compatible local artifacts,
- `CompositeDashboardAdapter` orchestrates fan-out to both output adapters from a single application boundary.

Rendering is triggered both from submission workflows and explicit script-driven generation.

## Consequences
- Positive:
  - Rendering concerns stay isolated in adapters, preserving hexagonal boundaries.
  - A single generation event can produce multiple output formats consistently.
  - Snapshot and adapter-level tests can validate output determinism.
- Trade-offs:
  - Two adapters increase template maintenance overhead.
  - Output divergence risk must be managed when evolving templates.
  - Local artifact generation alone does not automate publication.
- Follow-up implications:
  - Direct Confluence API publishing can be introduced later as another adapter strategy.
  - Template changes should continue to be guarded by regression snapshots/tests.

## Alternatives
- Generate HTML directly inside application use cases.
- Move rendering to a client-side web application using raw API payloads.
- Implement direct Confluence API publishing immediately, without local artifact-first staging.
