# XM QA Chatbot - Remaining Implementation Plan

## Scope

This document lists only unfinished work as of 2026-02-04.

---

## Current Focus

- Close remaining Phase 4 items for dashboard generation.
- Complete Phase 5 polish tasks (documentation, observability, security, performance, testing).

---

## Phase 4 Remaining Work: Dashboard Generation

### File Output
- [ ] Add a lightweight static file server for the generated HTML (e.g., `scripts/serve_dashboard.py` using `http.server`)
- [ ] Document the dashboard output path (`dashboard_html/`) and serving command in `README.md`
- [ ] Add a simple smoke check to ensure assets render (open `index`/overview page after generation)

### Testing
- [ ] Add HTML snapshot tests for `DashboardHtmlAdapter` output
  - [ ] Capture fixtures for overview/trends/team detail pages
  - [ ] Use a pytest snapshot library (decide between `pytest-regressions` or a minimal custom snapshot helper)
  - [ ] Normalize dynamic fields (timestamps, IDs) before snapshot comparison

### Phase 4 Exit Criteria
- [ ] Dashboard HTML can be served locally via a documented command
- [ ] Snapshot tests pass for all generated pages

---

## Phase 5 Remaining Work: Polish & Production Readiness

### Error Handling & Observability
- [ ] Select an error tracking provider (Sentry or OpenTelemetry exporter)
- [ ] Add configuration to `settings.py` + `.env.example` (DSN, environment, sampling)
- [ ] Wire error reporting in `main.py` and log structured context (request IDs, adapter names)
- [ ] Add alerting thresholds for failed LLM calls or storage failures

### Documentation
- [ ] Add ADRs for key decisions (use format in `docs/adr/`)
  - [ ] LLM provider selection + retry policy
  - [ ] Dashboard rendering pipeline (data ’ DTOs ’ HTML)
  - [ ] Storage strategy + migrations
- [ ] Create port API documentation (single `docs/ports.md`)
  - [ ] `DashboardPort`, `LLMPort`, `MetricsPort`, `StoragePort`
  - [ ] DTO definitions and expected error cases

### Security
- [ ] Implement API key management via environment variables (validate required keys on startup)
- [ ] Update `.env.example` with all required secret entries
- [ ] Ensure secrets are never logged (add redaction where needed)

### Performance
- [ ] Add database indexes for dashboard queries (e.g., `team_id`, `created_at`, `status`)
  - [ ] Create Alembic migration and verify with `sqlite3` query plan
- [ ] Implement LLM response caching (optional)
  - [ ] Cache key: prompt hash + model + temperature
  - [ ] Store in SQLite or in-memory (document TTL policy)
- [ ] Define dashboard caching strategy
  - [ ] Precompute aggregates per time window
  - [ ] Invalidate cache on new submission

### Testing & Quality Gate
- [ ] Generate coverage report (target >80%)
  - [ ] `pytest --cov=src --cov-report=term-missing`
- [ ] Run integration smoke tests
  - [ ] `pytest tests/integration/`
- [ ] Run local quality gate per `.clinerules/09-tooling-and-ci.md`
  - [ ] `ruff format .`
  - [ ] `ruff check . --fix` then `ruff check .`
  - [ ] `mypy src/ tests/`
  - [ ] `pytest tests/`

---

## Open Success Criteria

- [ ] Documentation complete (ADRs + `docs/ports.md` + README updates)
- [ ] Migration path to OpenAI validated (adapter retries + config documented)
- [ ] Coverage report generated (>80%) with gaps identified
- [ ] Integration smoke tests passing
- [ ] Dashboard HTML served locally via documented command

---

## Next Immediate Tasks

1. Draft ADRs and `docs/ports.md` (align with current ports and DTOs).
2. Implement dashboard HTML snapshot tests.
3. Generate coverage report and run integration smoke tests.
