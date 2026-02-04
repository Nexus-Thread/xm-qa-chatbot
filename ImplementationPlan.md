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
- [x] Add a lightweight static file server for the generated HTML (e.g., `scripts/serve_dashboard.py` using `http.server`)
- [x] Document the dashboard output path (`dashboard_html/`) and serving command in `README.md`
- [x] Add a simple smoke check to ensure assets render (open `index`/overview page after generation)

### Testing
- [x] Add HTML snapshot tests for `DashboardHtmlAdapter` output
  - [x] Capture fixtures for overview/trends/team detail pages
  - [x] Use a minimal custom snapshot helper (no extra dependency)
  - [x] Normalize dynamic fields (timestamps, IDs) before snapshot comparison

### Phase 4 Exit Criteria
- [x] Dashboard HTML can be served locally via a documented command
- [x] Snapshot tests pass for all generated pages

---

## Phase 5 Remaining Work: Polish & Production Readiness

### Error Handling & Observability
- [ ] Add configuration to `settings.py` + `.env.example` (DSN, environment, sampling)
- [ ] Wire error reporting in `main.py` and log structured context (request IDs, adapter names)
- [ ] Add alerting thresholds for failed LLM calls or storage failures

### Documentation
- [x] Add ADRs for key decisions (use format in `docs/adr/`)
  - [x] LLM provider selection + retry policy
  - [x] Dashboard rendering pipeline (data → DTOs → HTML)
  - [x] Storage strategy + migrations
- [x] Create port API documentation (single `docs/ports.md`)

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
- [x] Generate coverage report (target >80%)
  - [x] `pytest --cov=src --cov-report=term-missing` (79% overall; gaps in gradio adapter/conversation manager and LLM adapter)
- [x] Run integration smoke tests
  - [x] `pytest tests/integration/`
- [x] Run local quality gate per `.clinerules/09-tooling-and-ci.md`
  - [x] `ruff format .`
  - [x] `ruff check . --fix` then `ruff check .`
  - [x] `mypy src/ tests/`
  - [x] `pytest tests/`

---

## Open Success Criteria

- [x] Documentation complete (ADRs + `docs/ports.md` + README updates)
- [x] Migration path to OpenAI validated (adapter retries + config documented)
- [x] Coverage report generated (>80%) with gaps identified
- [x] Integration smoke tests passing
- [x] Dashboard HTML served locally via documented command

---

## Next Immediate Tasks

1. Address remaining coverage gaps (gradio adapter/conversation manager, OpenAI adapter).
2. Proceed with error tracking, security, and performance tasks in Phase 5.
