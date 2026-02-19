# Repository Audit Report — xm-qa-chatbot

**Date:** 2026-02-19
**Auditor:** Staff+ Engineer (automated audit)
**Commit:** 9823c376

---

## 1. Executive Summary

### Biggest Risks

- **No CI/CD pipeline exists.** Quality gates run only via local pre-commit hooks; there is zero server-side enforcement on push or PR.
- **`.env` committed to git** with `OPENAI_API_KEY=${OPENAI_API_KEY}` placeholder — teaches contributors to put secrets in tracked files.
- **No authentication or authorization** on the Gradio UI; anyone with network access can submit or overwrite project data.
- **Hard-coded business registry** (~400 lines in `builder.py`) — every project/stream change requires a code change and redeploy.
- **SQLite as sole persistence** — single-writer, no WAL mode, no connection-pool tuning; adequate for PoC but a scaling bottleneck.
- **Broad `except Exception`** in `_safe_fetch` (generate_monthly_report.py:162) silently swallows programming bugs alongside expected failures.
- **`DashboardRenderError` inherits `ValueError`** — domain exceptions using `ValueError` as base makes catch blocks fragile and leaky.
- **No dependency vulnerability scanning** — no `pip-audit`, `safety`, or Dependabot configuration.
- **CDN assets loaded without SRI hashes** — Tailwind and Plotly scripts fetched from CDNs with no integrity verification.

### Biggest Opportunities

- **98% coverage threshold already enforced** in pytest config — excellent foundation; extend this into CI.
- **Clean hexagonal architecture** consistently applied — ports/adapters separation is solid.
- **Pre-commit hooks already cover ruff + mypy** — low effort to mirror these in a CI pipeline.
- **Well-structured test suite** with unit, integration, and e2e layers — mirrors source layout.
- **ADRs exist** for key decisions — extend and enrich them as the project matures.
- **Pydantic settings adapter** already externalizes config — close to 12-factor compliance.

### Top 5 Actions Next

1. **Add a CI pipeline** (GitHub Actions) that runs the full quality gate on every push/PR.
2. **Remove `.env` from git**, add `.env.example`, and add `.env` to `.gitignore`.
3. **Add `pip-audit`** to pre-commit and CI for dependency vulnerability scanning.
4. **Externalize the stream/project registry** to a YAML/JSON config file loaded at startup.
5. **Narrow the `except Exception` clause** in `_safe_fetch` to catch only expected adapter errors.

## 2. Repository Map

### Tech Stack

| Layer | Technology | Version Constraint |
|---|---|---|
| Language | Python | ≥3.11 |
| Build | Hatchling | latest |
| Package manager | uv (lockfile: `uv.lock`) | — |
| UI framework | Gradio | ≥6.5.1 |
| LLM client | OpenAI Python SDK | ≥2.21.0 |
| ORM / DB | SQLAlchemy + SQLite | ≥2.0.46 |
| Migrations | Alembic | ≥1.18.4 |
| Config | Pydantic-settings | ≥2.13.0 |
| Templating | Jinja2 (via Gradio dep) | — |
| Linting | ruff | ≥0.15.1 |
| Type checking | mypy | ≥1.19.1 |
| Testing | pytest + pytest-cov + pytest-xdist | ≥9.0.2 |
| Pre-commit | pre-commit | ≥4.5.1 |

### High-Level Module Boundaries

```
src/qa_chatbot/
├── domain/              # Pure business logic, entities, value objects, exceptions
│   ├── entities/        # Submission, Project, BusinessStream, ReportingPeriod
│   ├── value_objects/   # ProjectId, TimeWindow, TestCoverageMetrics, SubmissionMetrics, etc.
│   ├── registries/      # StreamProjectRegistry (hard-coded builder)
│   └── exceptions.py    # Domain error hierarchy (DomainError → ValueError)
├── application/         # Use cases, ports, DTOs, services
│   ├── use_cases/       # ExtractStructuredData, SubmitProjectData, GenerateMonthlyReport, GetDashboardData
│   ├── ports/output/    # StoragePort, StructuredExtractionPort, DashboardPort, JiraMetricsPort, MetricsPort
│   ├── dtos/            # AppSettings, SubmissionCommand, ExtractionResult, MonthlyReport, DashboardData
│   └── services/        # EdgeCasePolicy, portfolio aggregate calculations
├── adapters/
│   ├── input/gradio/    # GradioAdapter (UI), ConversationManager (state machine), formatters, rate limiter
│   └── output/
│       ├── persistence/sqlite/  # SQLiteAdapter (StoragePort impl)
│       ├── llm/                 # OpenAI transport + StructuredExtractionAdapter
│       ├── dashboard/           # HTML, Confluence, Composite adapters (DashboardPort impl)
│       ├── jira_mock/           # MockJiraAdapter (JiraMetricsPort impl)
│       └── metrics/             # InMemoryMetricsAdapter (MetricsPort impl)
└── config/              # Logging configuration
```

### Data Flow

```
User (Gradio UI)
  → ConversationManager (state machine)
    → ExtractStructuredDataUseCase → StructuredExtractionPort → OpenAI API
    → SubmitProjectDataUseCase → StoragePort → SQLite DB
                                → DashboardPort → HTML files + Confluence artifacts
                                → MetricsPort → In-memory counters
```

### Entry Points

| Entry Point | File | Purpose |
|---|---|---|
| Main app | `src/qa_chatbot/main.py` | Wires all adapters, launches Gradio server |
| Dashboard gen | `scripts/generate_dashboard.py` | CLI script to regenerate dashboards from DB |
| DB seeding | `scripts/seed_database.py` | Populate DB with pseudo-random test data |
| Dashboard serve | `scripts/serve_dashboard.py` | Serve generated HTML dashboards locally |
| API submission | `scripts/submit_via_api.py` / `submit_data_direct.py` | Direct data submission scripts |
| Migrations | `migrations/env.py` + `alembic.ini` | Alembic schema migrations |

### Runtime Topology

Single-process Python application. Gradio runs an embedded HTTP server (default port 7860). SQLite database is a local file (`qa_chatbot.db`). Dashboard artifacts are written to `dashboard_html/`. External dependency: OpenAI-compatible API endpoint.

## 3. Audit Findings

### 3.1 Security

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| SEC-01 | **Critical** | Security | `.env` file with `OPENAI_API_KEY` placeholder is tracked in git. Contributors may commit real secrets. | `.env:2` — `OPENAI_API_KEY=${OPENAI_API_KEY}` | Remove `.env` from git, add to `.gitignore`, create `.env.example` with dummy values. | S | `sec/env-file-hygiene` |
| SEC-02 | **High** | Security | No authentication on Gradio UI. Any network-reachable user can submit/overwrite project data. | `src/qa_chatbot/main.py` — `app.launch()` with no `auth` param | Add Gradio `auth` parameter or reverse-proxy auth. Document in README. | M | `sec/gradio-auth` |
| SEC-03 | **High** | Security | CDN scripts loaded without Subresource Integrity (SRI) hashes. Supply-chain risk if CDN is compromised. | `adapters/output/dashboard/html/adapter.py:28-29` — Tailwind + Plotly URLs | Add `integrity` and `crossorigin` attributes to `<script>` tags in templates. | S | `sec/sri-hashes` |
| SEC-04 | **Medium** | Security | No dependency vulnerability scanning. No `pip-audit`, `safety`, or Dependabot config. | Absence of `.github/dependabot.yml`, no `pip-audit` in deps or pre-commit | Add `pip-audit` to dev deps and pre-commit. Add Dependabot config for GitHub. | S | `sec/dep-scanning` |
| SEC-05 | **Medium** | Security | Jira credentials (`jira_api_token`, `jira_username`) passed through settings and stored in adapter dataclass fields. No secret masking. | `adapters/output/jira_mock/adapter.py:14-17` — fields stored as plain strings | Mark secret fields with `repr=False`. Use `SecretStr` from Pydantic where applicable. | S | `sec/secret-masking` |
| SEC-06 | **Low** | Security | `alembic.ini` has `sqlalchemy.url = sqlite:///./qa_chatbot.db` hardcoded. If moved to production DB, credentials would leak. | `alembic.ini:63` | Use `env.py` to override URL from environment variables (partially done already). | S | `sec/alembic-url` |

### 3.2 Dependency Health

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| DEP-01 | **Medium** | Dependency | No automated dependency update policy. No Dependabot or Renovate configuration. | Absence of `.github/dependabot.yml` | Add Dependabot config for pip ecosystem with weekly schedule. | S | `deps/dependabot` |
| DEP-02 | **Low** | Dependency | `uv.lock` is present and committed — good practice. Lockfile ensures reproducible builds. | `uv.lock` in repo root | No action needed — positive finding. | — | — |
| DEP-03 | **Low** | Dependency | Jinja2 is used but only as a transitive dependency (via Gradio). No explicit pinning. | `adapters/output/dashboard/html/adapter.py:7` — imports `jinja2` | Consider adding `jinja2` as explicit dependency for dashboard rendering clarity. | S | `deps/explicit-jinja2` |

### 3.3 Architecture & Boundaries

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| ARCH-01 | **High** | Architecture | Hard-coded stream/project registry (~400 LOC) embedded in domain code. Business config changes require code changes. | `domain/registries/stream_project_registry/builder.py` — entire file | Extract registry data to a YAML/JSON config file. Load at startup via a config adapter. | L | `arch/externalize-registry` |
| ARCH-02 | **Medium** | Architecture | `DomainError` inherits from `ValueError` instead of `Exception`. This means `except ValueError` accidentally catches domain errors. | `domain/exceptions.py:4` — `class DomainError(ValueError)` | Rebase `DomainError` on `Exception`. Update all catch sites. | M | `arch/exception-hierarchy` |
| ARCH-03 | **Medium** | Architecture | `DashboardRenderError` inherits from `ValueError` instead of domain/adapter exception base. | `adapters/output/dashboard/exceptions.py:4` | Make `DashboardRenderError` inherit from a dedicated adapter error or `DomainError`. | S | `arch/dashboard-error-base` |
| ARCH-04 | **Medium** | Architecture | No input ports defined. Only output ports exist in `application/ports/output/`. The hexagonal pattern calls for input ports too. | `application/ports/` — no `input/` directory | Add input port protocols for use cases (e.g., `SubmitProjectDataInputPort`). Low urgency since use cases are directly injected. | M | `arch/input-ports` |
| ARCH-05 | **Medium** | Architecture | `ConversationManager` directly calls `build_default_stream_project_registry()` inside `_handle_project_id`, coupling input adapter to domain builder. | `adapters/input/gradio/conversation_manager.py:100` | Inject registry through constructor instead of building it per-call. | S | `arch/inject-registry` |
| ARCH-06 | **Low** | Architecture | `submit_project_data.py` catches only `ValueError` for dashboard errors (line 92). After ARCH-02/03 fix, this catch must be updated. | `application/use_cases/submit_project_data.py:92` | Update to catch `DashboardRenderError` or adapter base error explicitly. | S | Part of `arch/exception-hierarchy` |

### 3.4 Error Handling & Resilience

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| ERR-01 | **High** | Reliability | `_safe_fetch` catches `Exception` broadly, including `KeyboardInterrupt`-adjacent bugs. Masks programming errors. | `application/use_cases/generate_monthly_report.py:162` — comment says "Intentionally broad" | Narrow to `(DomainError, ConnectionError, TimeoutError)` or a defined adapter error base. | S | `err/narrow-safe-fetch` |
| ERR-02 | **Medium** | Reliability | No timeout configuration on SQLite operations. Long-running queries could block the Gradio event loop. | `adapters/output/persistence/sqlite/adapter.py:37` — `create_engine` without `connect_args` timeout | Add `connect_args={"timeout": 30}` to SQLite engine creation. | S | `err/sqlite-timeout` |
| ERR-03 | **Medium** | Reliability | No health check or readiness probe endpoint. If the LLM or DB is unreachable, there's no way to detect it externally. | `main.py` — no health route | Add a `/health` endpoint to Gradio (custom route) or a CLI health-check script. | M | `err/health-check` |
| ERR-04 | **Low** | Reliability | Dashboard generation failures during submission are logged but silently swallowed. User gets no feedback that dashboards failed. | `application/use_cases/submit_project_data.py:84-95` | Consider returning a warning/status alongside the saved submission. | S | `err/dashboard-feedback` |

### 3.5 Performance

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| PERF-01 | **Medium** | Performance | `GetDashboardDataUseCase._trend_series` issues N×M individual DB queries (projects × months). | `application/use_cases/get_dashboard_data.py:68-78` | Batch-query submissions by month list, then filter in-memory. | M | `perf/batch-trend-queries` |
| PERF-02 | **Medium** | Performance | `_extract_overall_test_cases` fetches all submissions for a month, then filters in Python. | `application/use_cases/generate_monthly_report.py:116-131` | Push aggregation to SQL query or cache per-month results. | M | `perf/aggregate-in-sql` |
| PERF-03 | **Low** | Performance | SQLite engine created without WAL mode. Concurrent reads during dashboard generation may contend with writes. | `adapters/output/persistence/sqlite/adapter.py:37` | Enable WAL: `engine.execute("PRAGMA journal_mode=WAL")` after creation. | S | `perf/sqlite-wal` |
| PERF-04 | **Low** | Performance | `Submission.__post_init__` creates a `SubmissionMetrics` instance purely for validation, then discards it. `.metrics` property creates another. | `domain/entities/submission.py:25-30` | Cache the validated metrics or validate inline without constructing a throwaway object. | S | `perf/submission-validation` |

### 3.6 Testing Strategy

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| TEST-01 | **Low** | Testing | 98% coverage threshold is excellent. However, coverage of `scripts/` directory is likely excluded. | `pyproject.toml:20` — `--cov=src/qa_chatbot` only | Add `scripts/` coverage or explicitly document exclusion. | S | `test/scripts-coverage` |
| TEST-02 | **Low** | Testing | Snapshot test `.prev` files exist alongside current snapshots — likely leftover from updates. | `tests/unit/adapters/snapshots/*.prev` — 3 files | Remove `.prev` files, add `*.prev` to `.gitignore`. | S | `test/clean-snapshots` |
| TEST-03 | **Low** | Testing | `TestCoverageMetrics` uses `__test__ = False` to prevent pytest collection. Works but is a naming smell. | `domain/value_objects/metrics.py:72` | Acceptable workaround; document in a comment why it's needed. Already has no issues. | — | — |
| TEST-04 | **Medium** | Testing | No contract tests for `StructuredExtractionPort` — the LLM adapter is tested via integration tests that require a live endpoint. | `tests/integration/adapters/test_openai_adapter.py` | Add unit tests with a mock OpenAI client to verify request/response mapping independently. | M | `test/llm-contract-tests` |

### 3.7 CI/CD

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| CI-01 | **Critical** | CI/CD | No CI/CD pipeline. No `.github/workflows/`, `.gitlab-ci.yml`, or equivalent. Quality gates are entirely local. | Absence of CI config files in repo root | Add GitHub Actions workflow mirroring the local quality gate (ruff, mypy, pytest). | M | `ci/github-actions` |
| CI-02 | **Medium** | CI/CD | No Makefile or task runner for reproducible local commands. Developers must remember the quality gate order. | Absence of `Makefile` or `justfile` | Add a `Makefile` with targets: `lint`, `typecheck`, `test`, `quality-gate`, `serve`. | S | `ci/makefile` |

### 3.8 Observability

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| OBS-01 | **Medium** | Observability | Metrics are in-memory only (`InMemoryMetricsAdapter`). Metrics are lost on restart. No export to Prometheus/StatsD. | `adapters/output/metrics/adapter.py` — entire file | Acceptable for PoC. Document as known limitation. Plan Prometheus adapter when needed. | M | `obs/metrics-export` |
| OBS-02 | **Low** | Observability | No structured log format (JSON). Logs use Python's default formatter with `extra={}` fields. | `config/logging_config.py` | Add JSON formatter option for production deployments. | S | `obs/json-logging` |
| OBS-03 | **Low** | Observability | No correlation IDs across request lifecycle. Cannot trace a single user conversation through logs. | `adapters/input/gradio/conversation_manager.py` — no request/session ID in logs | Add session ID to `ConversationSession` and include in all log `extra` fields. | M | `obs/correlation-ids` |

### 3.9 Configuration & Environments

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| CFG-01 | **Medium** | Config | `.env` file is tracked in git (see SEC-01). No `.env.example` for onboarding. | `.env` in repo, `.gitignore` does not list `.env` | Add `.env` to `.gitignore`, create `.env.example`. | S | `sec/env-file-hygiene` |
| CFG-02 | **Low** | Config | `alembic.ini` hardcodes `sqlalchemy.url`. The `env.py` can override it, but the default is misleading. | `alembic.ini:63` | Add comment noting that env var override is preferred. | S | `sec/alembic-url` |
| CFG-03 | **Low** | Config | Jira-related env vars (`JIRA_BASE_URL`, `JIRA_USERNAME`, `JIRA_API_TOKEN`) are not in `.env` file but are in `AppSettings`. | `application/dtos/app_settings.py:17-19` vs `.env` | Document all required env vars in `.env.example` and README. | S | `docs/env-vars` |

### 3.10 Documentation

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| DOC-01 | **Medium** | Docs | ADRs are minimal (3-5 lines each). Missing depth on alternatives, trade-offs, and migration paths. | `docs/adr/ADR-001*.md` through `ADR-004*.md` | Enrich ADRs with concrete alternatives evaluated, metrics, and follow-up actions. | S | `docs/enrich-adrs` |
| DOC-02 | **Medium** | Docs | README likely doesn't document all env vars, especially Jira and dashboard CDN settings. | `README.md` (inferred from `.env` gaps) | Add complete environment variable reference table. | S | `docs/env-vars` |
| DOC-03 | **Low** | Docs | No runbook or troubleshooting guide for common failure modes (LLM timeout, DB locked, dashboard render failure). | Absence of `docs/runbook.md` | Create a basic runbook covering top 5 failure scenarios. | S | `docs/runbook` |

### 3.11 Developer Experience

| ID | Severity | Category | Finding | Evidence | Recommendation | Effort | Suggested PR |
|---|---|---|---|---|---|---|---|
| DX-01 | **Medium** | DX | No `Makefile` or task runner. Developers must manually run `ruff format . && ruff check . --fix && ruff check . && mypy src/ tests/ && pytest tests/`. | Absence of `Makefile` | Add Makefile with standard targets. | S | `ci/makefile` |
| DX-02 | **Low** | DX | `builder.py` is ~400 lines of repetitive project definitions. Hard to review and maintain. | `domain/registries/stream_project_registry/builder.py` | Extract to data file (YAML). See ARCH-01. | L | `arch/externalize-registry` |
| DX-03 | **Low** | DX | Pre-commit config is well-structured. Positive finding. | `.pre-commit-config.yaml` | No action needed. | — | — |

## 4. Stop-the-Bleeding Fixes (Quick Wins)

### QW-1: Remove `.env` from git, create `.env.example`

- **Why:** Prevents accidental secret leakage. New contributors get a clear template.
- **What:** `git rm --cached .env`, add `.env` to `.gitignore`, create `.env.example` with all vars and placeholder values.
- **Where:** `.env`, `.gitignore`, new `.env.example`
- **Acceptance:** `git log --all --full-history -- .env` shows removal commit. `.env.example` contains all vars from `AppSettings`.

### QW-2: Add `Makefile` with quality gate targets

- **Why:** Eliminates guesswork; makes the quality gate a single command.
- **What:** Create `Makefile` with targets: `format`, `lint`, `typecheck`, `test`, `quality-gate` (runs all), `serve`.
- **Where:** New `Makefile` in repo root.
- **Acceptance:** `make quality-gate` runs the full pipeline described in `09-tooling-and-ci.md`.

```makefile
.PHONY: format lint typecheck test quality-gate serve

format:
	ruff format .
	ruff check . --fix

lint:
	ruff check .

typecheck:
	mypy src/ tests/

test:
	pytest tests/

quality-gate: format lint typecheck test

serve:
	python scripts/serve_dashboard.py
```

### QW-3: Add GitHub Actions CI workflow

- **Why:** Enforces quality gate on every push/PR. Currently zero server-side checks.
- **What:** Add `.github/workflows/ci.yml` running ruff, mypy, pytest on Python 3.11.
- **Where:** New `.github/workflows/ci.yml`
- **Acceptance:** CI passes on `main` branch. PRs show check status.

```yaml
name: CI
on: [push, pull_request]
jobs:
  quality-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv sync --frozen
      - run: uv run ruff format --check .
      - run: uv run ruff check .
      - run: uv run mypy src/ tests/
      - run: uv run pytest tests/ -x --timeout=300
```

### QW-4: Add `pip-audit` for dependency vulnerability scanning

- **Why:** No current mechanism to detect CVEs in dependencies.
- **What:** Add `pip-audit` to dev deps, add pre-commit hook, add CI step.
- **Where:** `pyproject.toml` (dev deps), `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
- **Acceptance:** `pip-audit` runs clean in CI. Known vulnerabilities (if any) are documented.

### QW-5: Narrow `except Exception` in `_safe_fetch`

- **Why:** Broad catch masks `TypeError`, `AttributeError`, and other programming bugs.
- **What:** Replace `except Exception` with `except (DomainError, ConnectionError, TimeoutError, OSError)`.
- **Where:** `src/qa_chatbot/application/use_cases/generate_monthly_report.py:162`
- **Acceptance:** Unit test confirms programming errors (e.g., `AttributeError`) propagate. Expected adapter errors are still caught.

### QW-6: Add SRI hashes to CDN script tags

- **Why:** Mitigates supply-chain attack if CDN is compromised.
- **What:** Generate SRI hashes for Tailwind and Plotly JS, add `integrity` and `crossorigin="anonymous"` attributes.
- **Where:** `src/qa_chatbot/adapters/output/dashboard/html/templates/*.html`
- **Acceptance:** HTML files include `integrity` attribute. Browser console shows no SRI violations.

### QW-7: Inject registry into ConversationManager

- **Why:** `_handle_project_id` rebuilds the registry on every message, coupling adapter to domain builder.
- **What:** Pass `StreamProjectRegistry` through `ConversationManager.__init__`. Remove inline `build_default_stream_project_registry()` call.
- **Where:** `src/qa_chatbot/adapters/input/gradio/conversation_manager.py:100`, `src/qa_chatbot/main.py`
- **Acceptance:** `ConversationManager` constructor accepts `registry` param. No direct import of `build_default_stream_project_registry` in adapter.

### QW-8: Clean up snapshot `.prev` files

- **Why:** Leftover files add noise to the repo.
- **What:** Delete `*.prev` files from `tests/unit/adapters/snapshots/`, add `*.prev` to `.gitignore`.
- **Where:** `tests/unit/adapters/snapshots/`, `.gitignore`
- **Acceptance:** No `.prev` files in repo. `.gitignore` prevents future commits.

### QW-9: Add SQLite timeout and WAL mode

- **Why:** Prevents indefinite blocking on locked DB; WAL improves concurrent read performance.
- **What:** Add `connect_args={"timeout": 30}` and execute `PRAGMA journal_mode=WAL` after engine creation.
- **Where:** `src/qa_chatbot/adapters/output/persistence/sqlite/adapter.py:37-38`
- **Acceptance:** Integration test confirms WAL mode is active. Timeout test confirms `OperationalError` after 30s.

### QW-10: Document all environment variables in `.env.example` and README

- **Why:** Jira settings, CDN URLs, and other vars are undocumented. New contributors must read source code.
- **What:** Create `.env.example` with all vars. Add env var reference table to README.
- **Where:** New `.env.example`, `README.md`
- **Acceptance:** Every field in `AppSettings` has a corresponding entry in `.env.example` with a description comment.

## 5. Remediation Plan (PR Roadmap)

| PR # | Title | Scope | Files/Areas | Dependencies | Risk | Effort | Acceptance Criteria | Rollback |
|---|---|---|---|---|---|---|---|---|
| 1 | `sec/env-file-hygiene` | Remove `.env` from git, add `.gitignore` entry, create `.env.example` | `.env`, `.gitignore`, new `.env.example` | None | Low | S | `.env` not tracked; `.env.example` lists all `AppSettings` fields with comments | Revert commit |
| 2 | `ci/makefile` | Add Makefile with quality gate targets | New `Makefile` | None | Low | S | `make quality-gate` runs format→lint→typecheck→test successfully | Delete `Makefile` |
| 3 | `ci/github-actions` | Add GitHub Actions CI workflow | New `.github/workflows/ci.yml` | PR #2 (uses same targets) | Low | M | CI passes on main branch; PR checks visible | Delete workflow file |
| 4 | `sec/dep-scanning` | Add `pip-audit` + Dependabot config | `pyproject.toml`, `.pre-commit-config.yaml`, new `.github/dependabot.yml`, CI update | PR #3 | Low | S | `pip-audit` passes in CI; Dependabot PRs appear weekly | Revert deps + config |
| 5 | `err/narrow-safe-fetch` | Narrow broad `except Exception` in `_safe_fetch` | `application/use_cases/generate_monthly_report.py` | None | Med | S | Unit test proves `AttributeError` propagates; expected errors still caught | Revert to `except Exception` |
| 6 | `sec/sri-hashes` | Add SRI hashes to CDN script tags in HTML templates | `adapters/output/dashboard/html/templates/*.html` | None | Low | S | HTML output includes `integrity` attributes; snapshot tests updated | Remove integrity attrs |
| 7 | `arch/inject-registry` | Inject `StreamProjectRegistry` into `ConversationManager` | `conversation_manager.py`, `main.py`, e2e tests | None | Low | S | No `build_default_stream_project_registry` import in conversation_manager; tests pass | Revert constructor change |
| 8 | `err/sqlite-hardening` | Add SQLite timeout + WAL mode | `adapters/output/persistence/sqlite/adapter.py`, integration tests | None | Low | S | WAL mode active (verified by integration test); timeout configured | Remove PRAGMA + timeout |
| 9 | `test/clean-snapshots` | Remove `.prev` snapshot files, update `.gitignore` | `tests/unit/adapters/snapshots/*.prev`, `.gitignore` | None | Low | S | No `.prev` files in repo; `.gitignore` includes `*.prev` | Revert gitignore |
| 10 | `docs/env-vars-and-onboarding` | Document all env vars in README + `.env.example`; create runbook | `README.md`, `.env.example`, new `docs/runbook.md` | PR #1 | Low | S | Every `AppSettings` field documented; runbook covers top 5 failure modes | Revert docs |
| 11 | `sec/secret-masking` | Add `repr=False` to secret fields; use `SecretStr` where applicable | `adapters/output/jira_mock/adapter.py`, `application/dtos/app_settings.py` | None | Low | S | `repr()` on adapter/settings objects does not show secrets; tests pass | Revert field annotations |
| 12 | `arch/exception-hierarchy` | Rebase `DomainError` on `Exception`; fix `DashboardRenderError` base; update all catch sites | `domain/exceptions.py`, `adapters/output/dashboard/exceptions.py`, `submit_project_data.py`, all `except ValueError` sites | None | Med | M | All tests pass; `except ValueError` no longer catches `DomainError`; ADR-005 documents decision |
| 13 | `test/llm-contract-tests` | Add unit-level contract tests for `StructuredExtractionPort` with mock OpenAI client | New test files in `tests/unit/adapters/` | None | Low | M | New tests verify request/response mapping without live endpoint; coverage maintained ≥98% |  Delete test files |
| 14 | `docs/enrich-adrs` | Expand ADR-001 through ADR-004 with alternatives, trade-offs, metrics | `docs/adr/ADR-001*.md` through `ADR-004*.md` | None | Low | S | Each ADR has ≥3 sentences per section (Context, Decision, Consequences, Alternatives) | Revert to previous ADR versions |
| 15 | `arch/externalize-registry` | Extract stream/project registry to YAML config file | New `config/registry.yaml`, refactored `builder.py`, new config adapter | PR #7 | Med | L | Registry loaded from YAML at startup; adding a project requires only YAML edit; ADR-005 documents change | Revert to hardcoded builder |
| 16 | `sec/gradio-auth` | Add optional authentication to Gradio UI | `adapters/input/gradio/adapter.py`, `settings.py`, `main.py`, `.env.example` | PR #1 | Med | M | Auth enabled when `GRADIO_AUTH_USERNAME`/`GRADIO_AUTH_PASSWORD` env vars set; README documents usage | Remove auth params |
| 17 | `obs/json-logging` | Add JSON log formatter option for production | `config/logging_config.py`, `application/dtos/app_settings.py` | None | Low | S | `LOG_FORMAT=json` env var produces JSON-structured log lines | Revert to default formatter |
| 18 | `obs/correlation-ids` | Add session ID to ConversationSession and propagate through logs | `conversation_manager.py`, `formatters.py`, use cases | PR #7 | Low | M | All log entries for a conversation share the same session ID in `extra` | Remove session ID field |
| 19 | `perf/batch-trend-queries` | Optimize N×M queries in `GetDashboardDataUseCase._trend_series` | `get_dashboard_data.py`, `storage_port.py` (new batch method), `sqlite/adapter.py` | None | Med | M | Single query per month replaces N×M queries; existing tests pass; benchmark shows improvement | Revert to per-project queries |
| 20 | `err/health-check` | Add health check endpoint or CLI probe | `main.py` or new `scripts/health_check.py` | None | Low | M | `/health` returns 200 with DB + config status; or CLI script exits 0/1 | Remove health route |

## 6. Quality Gates to Add

### Automated Gates Overview

| Gate | Tool | Where | Trigger | Blocking? |
|---|---|---|---|---|
| Code formatting | `ruff format --check .` | Pre-commit + CI | Every commit / every push | Yes |
| Linting | `ruff check .` | Pre-commit + CI | Every commit / every push | Yes |
| Type checking | `mypy src/ tests/` | Pre-commit + CI | Every commit / every push | Yes |
| Unit + integration tests | `pytest tests/ --cov-fail-under=98` | CI | Every push / PR | Yes |
| Dependency vulnerability scan | `pip-audit` | Pre-commit + CI | Every commit / weekly | Yes (CI), Advisory (pre-commit) |
| Dependency updates | Dependabot | GitHub | Weekly | No (creates PRs) |
| Secret detection | `detect-secrets` or `gitleaks` | Pre-commit + CI | Every commit / every push | Yes |
| Coverage threshold | `--cov-fail-under=98` (already configured) | CI | Every push / PR | Yes |

### Proposed Pre-commit Additions

```yaml
# Add to .pre-commit-config.yaml
  - repo: https://github.com/pypa/pip-audit
    rev: v2.7.3
    hooks:
      - id: pip-audit
        args: ["--require-hashes", "--disable-pip"]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.4
    hooks:
      - id: gitleaks
```

### Proposed CI Pipeline Structure

```
┌──────────────────────────────────────────────────┐
│  GitHub Actions — CI Workflow                     │
├──────────────────────────────────────────────────┤
│  1. Checkout + setup uv                          │
│  2. uv sync --frozen                             │
│  3. ruff format --check .           (format)     │
│  4. ruff check .                    (lint)       │
│  5. mypy src/ tests/                (typecheck)  │
│  6. pytest tests/ -x --cov-fail-under=98 (test)  │
│  7. pip-audit                       (security)   │
└──────────────────────────────────────────────────┘
```

### Coverage Strategy

- **Current:** 98% threshold on `src/qa_chatbot/` — excellent.
- **Recommended:** Maintain 98%. Add explicit exclusion comment for `scripts/` in `pyproject.toml` or add `scripts/` to coverage measurement.
- **Integration tests:** Run with `pytest.mark.integration` marker. Consider running in a separate CI job with extended timeout.
- **E2E tests:** Run with `pytest.mark.e2e` marker. Run in CI but allow failure as advisory (not blocking).

### Contract Testing (Future)

- Add contract tests for `StructuredExtractionPort` to validate LLM request/response format.
- Use `pytest-recording` or response fixtures to make OpenAI integration tests deterministic and CI-safe.

## 7. Open Questions / Assumptions

- **Is this deployed anywhere, or local-only?** The absence of Dockerfile, CI/CD, and production config suggests local/PoC use. If deployment is planned, the security and resilience findings become Critical. *Evidence to confirm:* presence of deployment scripts, infrastructure-as-code, or hosting documentation.

- **Is the Jira adapter truly a mock, or will it be replaced?** `MockJiraAdapter` uses deterministic hash-based pseudo-random data. If a real Jira integration is planned, the `JiraMetricsPort` contract and error handling need to be production-hardened. *Evidence to confirm:* product roadmap or ADR for Jira integration.

- **What is the expected user base and concurrency?** SQLite's single-writer model and in-memory metrics are fine for <10 concurrent users. Beyond that, PostgreSQL and persistent metrics become necessary. *Evidence to confirm:* usage metrics or deployment target documentation.

- **Are the hardcoded Jira filter templates in `builder.py` real?** The JQL patterns reference project keys like `AFFILIATE`, `BRIDGE`, `JTHALES` etc. If these are real Jira project keys, they should be externalized from the codebase. *Evidence to confirm:* cross-reference with actual Jira instance.

- **Is the `.env` file committed intentionally as a config template?** The `OPENAI_API_KEY=${OPENAI_API_KEY}` pattern suggests it's meant as a template, but it's not named `.env.example`. This ambiguity is a security risk. *Evidence to confirm:* ask the repository owner about intent.

- **Is Gradio share mode (`GRADIO_SHARE=true`) ever used in production?** Share mode creates a public Gradio tunnel with no authentication. If enabled in production, this is a Critical security exposure. *Evidence to confirm:* check deployment configurations.

- **Are the CDN versions for Tailwind and Plotly intentionally pinned?** `plotly-2.27.0.min.js` is pinned but Tailwind uses the generic `cdn.tailwindcss.com` (latest). This creates drift risk. *Evidence to confirm:* check if specific versions are intentional.

- **Is `overall_test_cases` used anywhere?** The field exists in `Submission`, `SubmissionMetrics`, and `SubmissionModel` but appears to always be `None` in the conversation flow. It may be a planned feature or dead code. *Evidence to confirm:* search for non-None assignments across the codebase and product requirements.

- **What is the OpenAI model configuration strategy?** `.env` defaults to `gpt-4o-mini`. Is this the intended production model, or is it a cost-saving dev default? Model choice affects extraction quality. *Evidence to confirm:* product requirements or cost analysis.

---

*End of audit report.*
