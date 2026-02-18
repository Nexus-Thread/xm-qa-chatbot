# HTML Dashboard Adapter Fix Plan

## Scope
Audit-driven remediation plan for `HtmlDashboardAdapter` and related templates/tests.

## Working Rule
- This file is the source of truth for the remediation effort.
- As todos progress, update the checkbox state in this file in the same commit before moving to the next task.
- If scope changes, update both the checklist and the related phase text to keep them aligned.

## Execution TODO Checklist

### Phase 1 — Quick Correctness + Safety
- [x] Fix overview template field names to `*_in_reporting_month`
- [x] Add regression tests for overview metric columns
- [x] Wrap template load/render/write failures with `DashboardRenderError(... ) from err`

### Phase 2 — Architecture Cleanup
- [x] Remove internal creation of adapters/use-cases from `HtmlDashboardAdapter`
- [x] Inject dependencies from composition root (`main.py`) via ports/factories
- [x] Ensure runtime wiring uses intended Jira provider (mock for now in all environments)

### Phase 3 — Hardening
- [ ] Strengthen smoke-check with required section/table/chart markers
- [ ] Use collision-safe atomic temp files (unique temp path per write)
- [ ] Optionally support local/self-hosted JS assets for offline reproducibility

## Prioritized Findings

1. **High: Adapter-to-adapter coupling and hardcoded mock dependency**
   - `HtmlDashboardAdapter` creates `MockJiraAdapter` and `GenerateMonthlyReportUseCase` internally.
   - Violates hexagonal guardrail (`Adapter -> Adapter`) and hardwires mock Jira metrics into runtime dashboard generation.

2. **High: Template/DTO field mismatch in overview**
   - `overview.html` references `*_last_month` fields.
   - DTO contract (`TestCoverageRow`) exposes `*_in_reporting_month` fields.
   - Can silently render empty/wrong values.

3. **Medium: Incomplete exception translation at adapter boundary**
   - Template loading, rendering, and file write operations are not consistently translated to `DashboardRenderError`.

4. **Medium: Smoke-check too weak**
   - Current check validates only generic HTML markers and misses meaningful rendering regressions.

5. **Medium: Gaps in test protection**
   - Overview test checks only a few strings and does not fully protect DTO-template contract correctness.

6. **Low/Medium: Atomic write collision risk**
   - Fixed `*.tmp` suffix can collide on concurrent renders.

7. **Low: CDN dependency for static artifacts**
   - Tailwind/Plotly from CDN introduces offline and availability/supply-chain risk.

---

## Remediation Phases

### Phase 1 — Quick Correctness + Safety
1. Fix overview template field names to `*_in_reporting_month`.
2. Add regression-oriented tests for overview metric columns (snapshot or targeted assertions).
3. Wrap template render/write/load failures and raise `DashboardRenderError(... ) from err`.

### Phase 2 — Architecture Cleanup
4. Remove internal creation of use cases/adapters from `HtmlDashboardAdapter`.
5. Inject dependencies from composition root (`main.py`) via ports/factories.
6. Ensure runtime wiring uses intended Jira provider (mock for now in all environments).

### Phase 3 — Hardening
7. Strengthen smoke-check with required section/table/chart markers.
8. Use collision-safe atomic temp files (unique temp path per write).
9. Optionally support local/self-hosted JS assets for offline reproducibility.

---

## Suggested Implementation Order
1. Phase 1 items 1-3
2. Phase 2 items 4-6
3. Phase 3 items 7-9

Run quality gate after implementation:
- `ruff format .`
- `ruff check . --fix`
- `ruff check .`
- `mypy src/ tests/`
- `pytest tests/`
