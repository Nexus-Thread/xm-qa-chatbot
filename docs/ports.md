# Ports Reference

## Overview
This document describes the application layer ports and their data contracts.

## Input ports

Location: `src/qa_chatbot/application/ports/input/`

### ExtractStructuredDataPort
- `extract_project_id(conversation: str, registry: StreamProjectRegistry) -> tuple[ProjectId, ExtractionConfidence]`
- `extract_time_window(conversation: str, current_date: date) -> TimeWindow`
- `extract_coverage(conversation: str) -> CoverageExtractionResult`
- `execute(conversation: str, current_date: date, registry: StreamProjectRegistry) -> ExtractionResult`
- `execute_with_history(request: HistoryExtractionRequest, current_date: date, registry: StreamProjectRegistry) -> ExtractionResult`

### SubmitProjectDataPort
- `execute(command: SubmissionCommand) -> Submission`

### GenerateMonthlyReportPort
- `execute(month: TimeWindow) -> MonthlyReport`

### GetDashboardDataPort
- `build_overview(month: TimeWindow) -> OverviewDashboardData`
- `build_project_detail(project_id: ProjectId, months: list[TimeWindow]) -> ProjectDetailDashboardData`
- `build_trends(projects: list[ProjectId], months: list[TimeWindow]) -> TrendsDashboardData`

## DashboardPort
Location: `src/qa_chatbot/application/ports/output/dashboard_port.py`

- `generate_overview(month: TimeWindow) -> Path`
  - Generates the overview dashboard for the given reporting month.
- `generate_project_detail(project_id: ProjectId, months: list[TimeWindow]) -> Path`
  - Generates a project detail dashboard for the given project across recent months.
- `generate_trends(projects: list[ProjectId], months: list[TimeWindow]) -> Path`
  - Generates a cross-project trends dashboard.

## StructuredExtractionPort
Location: `src/qa_chatbot/application/ports/output/structured_extraction_port.py`

- `extract_project_id(conversation: str, registry: StreamProjectRegistry) -> tuple[ProjectId, ExtractionConfidence]`
- `extract_time_window(conversation: str, current_date: date) -> TimeWindow`
- `extract_coverage(conversation: str) -> CoverageExtractionResult`
- `extract_with_history(request: HistoryExtractionRequest, current_date: date, registry: StreamProjectRegistry) -> ExtractionResult`

Expected errors: `LLMExtractionError`, `AmbiguousExtractionError`

## MetricsPort
Location: `src/qa_chatbot/application/ports/output/metrics_port.py`

- `record_submission(project_id: ProjectId, time_window: TimeWindow) -> None`
- `record_llm_latency(operation: str, elapsed_ms: float) -> None`

## StoragePort
Location: `src/qa_chatbot/application/ports/output/storage_port.py`

- `save_submission(submission: Submission) -> None`
- `get_submissions_by_project(project_id: ProjectId, month: TimeWindow) -> list[Submission]`
- `get_all_projects() -> list[ProjectId]`
- `get_submissions_by_month(month: TimeWindow) -> list[Submission]`
- `get_recent_months(limit: int) -> list[TimeWindow]`

Expected errors: `InvalidConfigurationError` (startup), storage adapter exceptions translated at adapter boundaries.

## DTOs
Location: `src/qa_chatbot/application/dtos/`

### SubmissionCommand
Represents validated input used by `SubmitProjectDataUseCase`.

Fields:
- `project_id: ProjectId`
- `time_window: TimeWindow`
- `metrics: SubmissionMetrics`
- `raw_conversation: str | None`
- `created_at: datetime | None`

### ExtractionResult
Represents extracted structured data from the LLM adapter.

Fields:
- `project_id: ProjectId`
- `time_window: TimeWindow`
- `metrics: SubmissionMetrics`

### Dashboard DTOs
From `dashboard_data.py`:

- `ProjectOverviewCard`: summary per project for the overview page.
- `OverviewDashboardData`: reporting month + list of `ProjectOverviewCard`.
- `ProjectMonthlySnapshot`: per-month metrics for a project.
- `ProjectDetailDashboardData`: project ID + list of `ProjectMonthlySnapshot`.
- `TrendSeries`: label + list of values across months.
- `TrendsDashboardData`: project list, months, QA metric series, project metric series.
