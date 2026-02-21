"""Submit test coverage data directly via use cases (bypassing Gradio UI)."""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

from qa_chatbot.adapters.input import EnvSettingsAdapter
from qa_chatbot.adapters.output import HtmlDashboardAdapter, InMemoryMetricsAdapter, MockJiraAdapter, SQLiteAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry


def _echo(message: str = "") -> None:
    """Write a user-facing message to stdout."""
    sys.stdout.write(f"{message}\n")


def submit_test_coverage_data() -> None:
    """Submit test coverage data directly through use cases."""
    settings = EnvSettingsAdapter().load()

    _echo("=" * 60)
    _echo("SUBMITTING DATA DIRECTLY TO USE CASES")
    _echo("=" * 60)
    _echo("\nData to submit:")
    _echo("  Project: Client Trading (client_journey stream)")
    _echo("  Period: 2026-01")
    _echo("  Manual Total: 1000")
    _echo("  Manual Created: 100")
    _echo("  Manual Updated: 120")
    _echo("  Automated Total: 500")
    _echo("  Automated Created: 50")
    _echo("  Automated Updated: 30")
    _echo("=" * 60 + "\n")

    # Initialize adapters (same as in main.py)
    _echo("Step 1: Initializing storage adapter...")
    storage = SQLiteAdapter(
        database_url=settings.database_url,
        echo=settings.database_echo,
        timeout_seconds=settings.database_timeout_seconds,
    )
    storage.initialize_schema()
    _echo("✅ Storage initialized\n")

    _echo("Step 2: Initializing dashboard adapter...")
    dashboard_adapter = _build_dashboard_adapter(settings=settings, storage=storage)
    _echo("✅ Dashboard adapter initialized\n")

    _echo("Step 3: Initializing metrics adapter...")
    metrics_adapter = InMemoryMetricsAdapter()
    _echo("✅ Metrics adapter initialized\n")

    _echo("Step 4: Creating submission command...")
    command = _build_submission_command()
    _echo("✅ Submission command created\n")

    _echo("Step 5: Submitting data...")
    submitter = SubmitProjectDataUseCase(
        storage_port=storage,
        dashboard_port=dashboard_adapter,
        metrics_port=metrics_adapter,
    )
    result = submitter.execute(command)
    _echo("✅ Data submitted successfully!\n")

    if result.has_warnings:
        _echo("⚠️  Submission saved with dashboard warnings:")
        for warning in result.warnings:
            _echo(f"   - {warning}")
        _echo()

    _echo("=" * 60)
    _echo("✅ SUCCESS: Data has been saved to the database!")
    _echo("=" * 60)
    _echo("\nNext steps:")
    _echo("  1. View the dashboard: python scripts/serve_dashboard.py")
    _echo("  2. Check the database: sqlite3 qa_chatbot.db")
    _echo("  3. Query submissions:")
    _echo("     SELECT * FROM submissions WHERE project_id = 'client_trading';")


def _build_dashboard_adapter(settings: object, storage: SQLiteAdapter) -> HtmlDashboardAdapter:
    registry = build_default_stream_project_registry()
    edge_case_policy = EdgeCasePolicy()
    jira_adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url=settings.jira_base_url,
        jira_username=settings.jira_username,
        jira_api_token=settings.jira_api_token,
    )
    report_use_case = GenerateMonthlyReportUseCase(
        storage_port=storage,
        jira_port=jira_adapter,
        registry=registry,
        timezone="UTC",
        edge_case_policy=edge_case_policy,
    )
    dashboard_data_use_case = GetDashboardDataUseCase(storage_port=storage)
    dashboard_output_dir = Path(settings.dashboard_output_dir)
    return HtmlDashboardAdapter(
        get_dashboard_data_use_case=dashboard_data_use_case,
        generate_monthly_report_use_case=report_use_case,
        output_dir=dashboard_output_dir,
        tailwind_script_src=settings.dashboard_tailwind_script_src,
        plotly_script_src=settings.dashboard_plotly_script_src,
    )


def _build_submission_command() -> SubmissionCommand:
    project_id = ProjectId.from_raw("client_trading")
    time_window = TimeWindow.from_year_month(2026, 1)
    test_coverage = TestCoverageMetrics(
        manual_total=1000,
        automated_total=500,
        manual_created_in_reporting_month=100,
        manual_updated_in_reporting_month=120,
        automated_created_in_reporting_month=50,
        automated_updated_in_reporting_month=30,
        percentage_automation=33.33,
    )
    return SubmissionCommand(
        project_id=project_id,
        time_window=time_window,
        metrics=SubmissionMetrics(
            test_coverage=test_coverage,
            overall_test_cases=None,
            supported_releases_count=None,
        ),
        raw_conversation="Direct API submission via script",
        created_at=datetime.now(UTC),
    )


if __name__ == "__main__":
    submit_test_coverage_data()
