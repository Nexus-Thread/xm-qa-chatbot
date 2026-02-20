# IMPLEMENTATION PLAN

Source: `docs/AUDIT-REPORT.md` (2026-02-19)

This is a living checklist. Each top-level checkbox is one implementation chunk that should be completed in a focused PR.

## How to use this plan

- Keep each chunk small enough to review and ship independently.
- Mark a chunk as done only when its acceptance criteria are met.
- Run the local quality gate for every code change:
  - `ruff format .`
  - `ruff check . --fix`
  - `ruff check .`
  - `mypy src/ tests/`
  - `pytest tests/`

---

## Phase 1 — Critical security + CI foundations

- [x] **CH-01: Env file hygiene** (`SEC-01`, `CFG-01`)
  - Deliverables: remove tracked `.env`, add `.env` to `.gitignore`, create `.env.example`
  - Acceptance: `.env` is not tracked; `.env.example` includes all required settings keys

- [x] **CH-02: Add Makefile quality gate targets** (`CI-02`, `DX-01`)
  - Deliverables: `Makefile` targets `format`, `lint`, `typecheck`, `test`, `quality-gate`, `serve`
  - Acceptance: `make quality-gate` runs the same sequence as project rules

- [ ] **CH-03: Add GitHub Actions CI workflow** (`CI-01`)
  - Deliverables: `.github/workflows/ci.yml` running format-check, lint, typecheck, tests
  - Acceptance: workflow triggers on push/PR and passes on main

- [ ] **CH-04: Dependency vulnerability scanning** (`SEC-04`, `DEP-01`)
  - Deliverables: `pip-audit` in dev toolchain + pre-commit + CI; add Dependabot config
  - Acceptance: pipeline includes vulnerability scan; dependency update bot opens scheduled PRs

- [ ] **CH-05: Add Gradio authentication** (`SEC-02`)
  - Deliverables: optional auth via env vars in settings + wiring in launch path
  - Acceptance: when auth env vars are set, UI requires credentials

---

## Phase 2 — Fast reliability hardening

- [x] **CH-06: Narrow broad exception handling in monthly report fetch** (`ERR-01`)
  - Deliverables: replace broad `except Exception` with expected exception set
  - Acceptance: programming errors propagate; expected operational failures remain handled

- [x] **CH-07: SQLite timeout + WAL mode** (`ERR-02`, `PERF-03`)
  - Deliverables: SQLite connection timeout and WAL initialization
  - Acceptance: adapter config includes timeout; integration tests verify behavior

- [ ] **CH-08: Surface dashboard generation warning to caller** (`ERR-04`)
  - Deliverables: submission result includes warning/status when dashboard generation fails
  - Acceptance: user-visible outcome distinguishes saved data vs dashboard failure

- [ ] **CH-09: Add health check path/script** (`ERR-03`)
  - Deliverables: `/health` endpoint or CLI probe for DB + core dependency status
  - Acceptance: returns clear success/failure and can be used by ops checks

---

## Phase 3 — Architecture boundary corrections

- [x] **CH-10: Fix exception hierarchy base classes** (`ARCH-02`, `ARCH-03`, `ARCH-06`)
  - Deliverables: `DomainError` no longer derives from `ValueError`; update dashboard error base and catch sites
  - Acceptance: no catch logic depends on `ValueError` for domain/adapter failures

- [x] **CH-11: Inject stream/project registry into ConversationManager** (`ARCH-05`)
  - Deliverables: registry passed via constructor from composition root
  - Acceptance: no per-call registry builder invocation in input adapter

- [x] **CH-12: Add input ports in application layer** (`ARCH-04`)
  - Deliverables: `application/ports/input/` protocols for use cases and updated wiring
  - Acceptance: driving adapters depend on input port contracts rather than concrete classes

---

## Phase 4 — Testing and developer experience

- [ ] **CH-13: Add contract tests for structured extraction port** (`TEST-04`)
  - Deliverables: unit-level mapping tests using mocked OpenAI interactions
  - Acceptance: request/response contract validated without live endpoint

- [ ] **CH-14: Clean up snapshot leftovers** (`TEST-02`)
  - Deliverables: remove `*.prev` snapshot files and ignore future leftovers
  - Acceptance: repo contains no `.prev` snapshot artifacts

- [x] **CH-15: Clarify scripts coverage decision** (`TEST-01`)
  - Deliverables: either include `scripts/` in coverage scope or document explicit exclusion
  - Acceptance: coverage strategy is explicit and documented

---

## Phase 5 — Documentation, config clarity, and observability

- [x] **CH-16: Document all environment variables** (`DOC-02`, `CFG-03`, `QW-10`)
  - Deliverables: README env table + `.env.example` aligned with `AppSettings`
  - Acceptance: every settings field is documented with purpose/default/example

- [ ] **CH-17: Add operations runbook** (`DOC-03`)
  - Deliverables: `docs/runbook.md` for top operational failures and recovery steps
  - Acceptance: includes at least LLM timeout, DB lock, dashboard render failure scenarios

- [ ] **CH-18: Enrich ADRs with full decision records** (`DOC-01`)
  - Deliverables: update ADR-001..ADR-004 with Context, Decision, Consequences, Alternatives
  - Acceptance: each ADR explains trade-offs and follow-up implications

- [ ] **CH-19: Add JSON logging option** (`OBS-02`)
  - Deliverables: production-selectable JSON log formatter via settings
  - Acceptance: logs are structured when JSON mode enabled

- [ ] **CH-20: Add conversation correlation IDs in logs** (`OBS-03`)
  - Deliverables: session/request ID propagation from input adapter through logs
  - Acceptance: a single conversation can be traced end-to-end via shared ID

---

## Phase 6 — Performance and strategic refactor

- [ ] **CH-21: Batch trend queries for dashboard use case** (`PERF-01`)
  - Deliverables: replace N×M query pattern with batch retrieval strategy
  - Acceptance: fewer DB round trips and measured improvement on representative data

- [ ] **CH-22: Move monthly aggregation closer to SQL** (`PERF-02`)
  - Deliverables: avoid full-month Python-side filtering when computing totals
  - Acceptance: aggregation path is measurably faster and correctness is test-covered

- [ ] **CH-23: Remove redundant submission metrics object creation** (`PERF-04`)
  - Deliverables: avoid throwaway validation object in `Submission` initialization
  - Acceptance: same validation guarantees with lower object churn

- [ ] **CH-24: Externalize stream/project registry to data config** (`ARCH-01`, `DX-02`)
  - Deliverables: YAML/JSON registry source + loader adapter + startup wiring
  - Acceptance: adding/changing stream/project mappings no longer requires code edits

---

## Optional backlog (after core plan)

- [ ] **CH-25: Add SRI for dashboard CDN assets** (`SEC-03`)
- [ ] **CH-26: Secret masking for Jira-related settings/adapter fields** (`SEC-05`)
- [ ] **CH-27: Clarify Alembic URL override documentation** (`SEC-06`, `CFG-02`)
- [ ] **CH-28: Add explicit `jinja2` dependency** (`DEP-03`)
- [ ] **CH-29: Persist/export metrics beyond in-memory adapter** (`OBS-01`)
