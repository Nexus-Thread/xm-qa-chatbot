# Ports Reference

## Overview
This document describes the application layer ports and their data contracts.

## DashboardPort
Location: `src/qa_chatbot/application/ports/output/dashboard_port.py`

- `generate_overview(month: TimeWindow) -> Path`
  - Generates the overview dashboard for the given reporting month.
- `generate_team_detail(team_id: TeamId, months: list[TimeWindow]) -> Path`
  - Generates a team detail dashboard for the given team across recent months.
- `generate_trends(teams: list[TeamId], months: list[TimeWindow]) -> Path`
  - Generates a cross-team trends dashboard.

## LLMPort
Location: `src/qa_chatbot/application/ports/output/llm_port.py`

- `extract_team_id(conversation: str) -> TeamId`
- `extract_time_window(conversation: str, current_date: date) -> TimeWindow`
- `extract_qa_metrics(conversation: str) -> QAMetrics`
- `extract_project_status(conversation: str) -> ProjectStatus`
- `extract_daily_update(conversation: str) -> DailyUpdate`
- `extract_with_history(conversation: str, history: list[dict[str, str]] | None, current_date: date) -> ExtractionResult`

Expected errors: `LLMExtractionError`, `AmbiguousExtractionError`

## MetricsPort
Location: `src/qa_chatbot/application/ports/output/metrics_port.py`

- `record_submission(team_id: TeamId, time_window: TimeWindow) -> None`
- `record_llm_latency(operation: str, elapsed_ms: float) -> None`

## StoragePort
Location: `src/qa_chatbot/application/ports/output/storage_port.py`

- `save_submission(submission: Submission) -> None`
- `get_submissions_by_team(team_id: TeamId, month: TimeWindow) -> list[Submission]`
- `get_all_teams() -> list[TeamId]`
- `get_submissions_by_month(month: TimeWindow) -> list[Submission]`
- `get_recent_months(limit: int) -> list[TimeWindow]`

Expected errors: `InvalidConfigurationError` (startup), storage adapter exceptions translated at adapter boundaries.

## DTOs
Location: `src/qa_chatbot/application/dtos/`

### SubmissionCommand
Represents validated input used by `SubmitTeamDataUseCase`.

Fields:
- `team_id: TeamId`
- `time_window: TimeWindow`
- `qa_metrics: QAMetrics | None`
- `project_status: ProjectStatus | None`
- `daily_update: DailyUpdate | None`
- `raw_conversation: str | None`
- `created_at: datetime | None`

### ExtractionResult
Represents extracted structured data from the LLM adapter.

Fields:
- `team_id: TeamId`
- `time_window: TimeWindow`
- `qa_metrics: QAMetrics | None`
- `project_status: ProjectStatus | None`
- `daily_update: DailyUpdate | None`

### Dashboard DTOs
From `dashboard_data.py`:

- `TeamOverviewCard`: summary per team for the overview page.
- `OverviewDashboardData`: reporting month + list of `TeamOverviewCard`.
- `TeamMonthlySnapshot`: per-month metrics for a team.
- `TeamDetailDashboardData`: team ID + list of `TeamMonthlySnapshot`.
- `TrendSeries`: label + list of values across months.
- `TrendsDashboardData`: team list, months, QA metric series, project metric series.
