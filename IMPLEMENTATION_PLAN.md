# IMPLEMENTATION PLAN

Source: `docs/AUDIT-REPORT.md` (2026-02-19)

This is a living checklist. Each top-level checkbox is one implementation chunk that should be completed in a focused PR.

Only **pending** chunks are listed below. Completed chunks were removed from this active plan.

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

- [x] **CH-08: Surface dashboard generation warning to caller** (`ERR-04`)
  - Deliverables: submission result includes warning/status when dashboard generation fails
  - Acceptance: user-visible outcome distinguishes saved data vs dashboard failure

- [ ] **CH-09: Add health check path/script** (`ERR-03`)
  - Deliverables: `/health` endpoint or CLI probe for DB + core dependency status
  - Acceptance: returns clear success/failure and can be used by ops checks

---

## Phase 5 — Documentation, config clarity, and observability

- [ ] **CH-17: Add operations runbook** (`DOC-03`)
  - Deliverables: `docs/runbook.md` for top operational failures and recovery steps
  - Acceptance: includes at least LLM timeout, DB lock, dashboard render failure scenarios

---

## Phase 6 — Performance and strategic refactor

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
