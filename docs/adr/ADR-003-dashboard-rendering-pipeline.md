# ADR-003: Dashboard Rendering Pipeline

## Context
The dashboard must be generated as static HTML for sharing and inspection. We need a deterministic pipeline that transforms stored submissions into templated views.

## Decision
Use `GetDashboardDataUseCase` to aggregate data into dashboard DTOs and a `GenerateMonthlyReportUseCase` payload for overview rendering.

Use a dual-output adapter strategy:
- `HtmlDashboardAdapter` renders browser-ready static HTML files
- `ConfluenceDashboardAdapter` renders Confluence-ready local artifacts (`*.confluence.html`)
- `CompositeDashboardAdapter` fans out each dashboard generation call to both adapters

Rendering occurs after each submission via `SubmitTeamDataUseCase`, and can also be triggered by `scripts/generate_dashboard.py`.

## Consequences
Dashboard generation remains deterministic and testable in the adapter layer. The same submission event now produces two local output formats from one application boundary (`DashboardPort`).

Confluence publishing is intentionally local-first in this phase: artifacts are generated for review/import, while direct Confluence API publishing remains a future extension behind adapter boundaries.

## Alternatives
- Generate HTML directly in the use case layer
- Client-side rendering from raw API responses
- Implement direct Confluence API publishing immediately in this phase
