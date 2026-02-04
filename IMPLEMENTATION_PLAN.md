# Monthly QA Summary Generator — Implementation Plan

## Goal
Deliver full compliance with `REQUIREMENTS.md` for the monthly QA summary report, including configuration-driven sources, portfolio aggregates, Jira/report link scaffolding, regression time formatting, and completeness reporting.

## Current State (Audit Summary)
### Implemented
- HTML overview report with Section A/B, metadata, completeness summary, and coverage headline.
- Domain objects for streams/projects/reporting period/metrics/regression blocks/priority buckets.
- Monthly report use case with mocked Jira + release adapters.
- Stream registry seeded from requirements.
- Chatbot extraction of test coverage + portfolio total.

### Gaps vs requirements
1. **Versioned config file (YAML/JSON)** for streams/projects, per-project sources, priority mapping, regression suite definitions.
2. **Jira source configuration + query templates** (priority buckets, QA-found logic, time window selection, link templates).
3. **Supported releases** source selection (Jira releases / release calendar / manual override).
4. **Regression time formatting** (minutes → human units + annotations).
5. **Portfolio aggregate row** (totals + averages + inclusion rules + rounding).
6. **Stream grouping/ordering** in report rendering (stream headers or grouped sections).
7. **Completeness detail granularity** (missing cells/sources per project/metric).
8. **Centralized rounding + edge-case policies** (automation %, leakage %).

## Proposed Implementation Sequence
### 1) Configuration Layer (Foundation)
- Add `qa_chatbot/config/reporting_config.py` with Pydantic models for:
  - Streams/projects (ordering, active flags)
  - Jira sources (project keys/components, issue types, QA-found logic)
  - Priority bucket mapping (P1–P2 vs P3–P4)
  - Defect leakage numerator/denominator scope
  - Supported releases source selection
  - Regression suite definitions
  - Edge-case policies (automation %, leakage %, rounding)
- Create `config/reporting_config.yaml` in repo with the default stream/project list and stubbed source definitions.
- Add config loader + validation errors routed to `InvalidConfigurationError`.

**Session Update (2026-02-04)**
- ✅ Added `qa_chatbot/config/reporting_config.py` with Pydantic models and YAML loader/validation.
- ✅ Added `config/reporting_config.yaml` with stream/project defaults and Jira/release stubs.
- ✅ Added `pyyaml` dependency and exported `ReportingConfig` via `qa_chatbot/config/__init__.py`.

**Session Update (2026-02-04, later)**
- ✅ Wired `ReportingConfig` into the HTML dashboard report generation pipeline.
- ✅ Updated Jira and release mock adapters to read config values and templates.
- ✅ Aligned reporting config project IDs with the stream registry and added sample Jira source stubs.

**Session Update (2026-02-04, aggregation/formats)**
- ✅ Added reporting calculations helpers (edge-case policies, regression formatting scaffolding).
- ✅ Wired edge-case policy into report generation.
- ✅ Added portfolio aggregate calculation scaffolding and portfolio row rendering.
- ✅ Added structured completeness reporting details in the overview template.
- ✅ Added regression suite config stubs and wired formatted regression entries into report output.
- ✅ Applied defect leakage edge-case handling in report output.
- ✅ Ran quality gate: ruff format/check, mypy (after adding types-PyYAML), pytest.
- ✅ Resolved mypy pre-commit issues (restored AppSettings ignores) and re-ran mypy/pytest successfully.
- ✅ Added types-PyYAML to the pre-commit mypy hook dependencies.

### 2) Jira + Release Source Scaffolding
- Update Jira port to accept config context and expose link builders per metric.
- Expand mock Jira adapter to honor config (priority mapping, QA-found logic, leakage scopes).
- Add release support adapter that reads from config (manual override now, placeholders for future Jira/releases).

### 3) Computation Utilities
- Add aggregation helpers for:
  - Portfolio totals/averages (supported releases, bug/incident buckets, leakage)
  - Inclusion rules for averages (active-only, skip missing vs include zeros)
- Add leakage + automation calculators with configurable edge-case policies.
- Expand completeness reporting to record missing cells per project/metric.

### 4) Regression Time Formatting
- Implement formatter for `RegressionTimeBlock`:
  - Canonical minutes → seconds/minutes/hours
  - Preserve annotations (threads/context counts/notes)
  - Support free-text override
- Wire formatted entries into `QualityMetricsRow` DTO.

### 5) HTML Rendering Enhancements
- Add “All Streams, average” row to Section A and Section B.
- Group rows by stream (optional stream header rows).
- Render leakage as `(n/d) * 100 = x%` and add links when available.
- Ensure automation % renders to 2 decimals with configured edge-case behavior.

### 6) Tests + Documentation
- Unit tests for config loading, aggregation math, leakage/automation edge cases.
- Snapshot updates for overview HTML.
- README/doc updates: configuration format + how to run report generation.

## Acceptance Checklist (mapped to REQUIREMENTS.md)
- [x] Config-driven stream/project registry + sources
- [x] Jira mock returns bucketed counts + filter links
- [x] Release support source selection implemented
- [x] Defect leakage + automation % calculations with edge cases
- [x] Regression time formatted from minutes with annotations
- [x] Portfolio aggregate row in both sections
- [x] Completeness status with explicit missing fields
- [x] HTML rendering passes updated snapshots

## Next Step
Begin with the configuration layer and wire mocks to read config values. After that, implement portfolio aggregates + regression formatting, then adjust rendering and tests.
