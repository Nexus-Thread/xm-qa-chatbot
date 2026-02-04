# ADR-003: Dashboard Rendering Pipeline

## Context
The dashboard must be generated as static HTML for sharing and inspection. We need a deterministic pipeline that transforms stored submissions into templated views.

## Decision
Use `GetDashboardDataUseCase` to aggregate data into dashboard DTOs and `HtmlDashboardAdapter` to render Jinja templates into static files. Rendering occurs after each submission via `SubmitTeamDataUseCase`.

## Consequences
Dashboard generation is deterministic and testable with snapshot fixtures. The adapter layer owns template rendering and output paths.

## Alternatives
- Generate HTML directly in the use case layer
- Client-side rendering from raw API responses
