"""Submit test coverage data directly via use cases (bypassing Gradio UI)."""

from __future__ import annotations

import traceback
from datetime import UTC, datetime
from pathlib import Path

from qa_chatbot.adapters.input import EnvSettingsAdapter
from qa_chatbot.adapters.output import HtmlDashboardAdapter, InMemoryMetricsAdapter, MockJiraAdapter, SQLiteAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry

# ruff: noqa: T201


def submit_test_coverage_data() -> None:
    """Submit test coverage data directly through use cases."""
    settings = EnvSettingsAdapter().load()

    print("=" * 60)
    print("SUBMITTING DATA DIRECTLY TO USE CASES")
    print("=" * 60)
    print("\nData to submit:")
    print("  Project: Client Trading (client_journey stream)")
    print("  Period: 2026-01")
    print("  Manual Total: 1000")
    print("  Manual Created: 100")
    print("  Manual Updated: 120")
    print("  Automated Total: 500")
    print("  Automated Created: 50")
    print("  Automated Updated: 30")
    print("=" * 60 + "\n")

    # Initialize adapters (same as in main.py)
    print("Step 1: Initializing storage adapter...")
    storage = SQLiteAdapter(database_url=settings.database_url, echo=settings.database_echo)
    storage.initialize_schema()
    print("✅ Storage initialized\n")

    print("Step 2: Initializing dashboard adapter...")
    dashboard_adapter = _build_dashboard_adapter(settings=settings, storage=storage)
    print("✅ Dashboard adapter initialized\n")

    print("Step 3: Initializing metrics adapter...")
    metrics_adapter = InMemoryMetricsAdapter()
    print("✅ Metrics adapter initialized\n")

    print("Step 4: Creating submission command...")
    command = _build_submission_command()
    print("✅ Submission command created\n")

    print("Step 5: Submitting data...")
    submitter = SubmitProjectDataUseCase(
        storage_port=storage,
        dashboard_port=dashboard_adapter,
        metrics_port=metrics_adapter,
    )

    try:
        submitter.execute(command)
        print("✅ Data submitted successfully!\n")

        print("=" * 60)
        print("✅ SUCCESS: Data has been saved to the database!")
        print("=" * 60)
        print("\nNext steps:")
        print("  1. View the dashboard: python scripts/serve_dashboard.py")
        print("  2. Check the database: sqlite3 qa_chatbot.db")
        print("  3. Query submissions:")
        print("     SELECT * FROM submissions WHERE project_id = 'client_trading';")

    except Exception as e:
        print(f"❌ ERROR during submission: {e}")
        traceback.print_exc()
        raise


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
    try:
        submit_test_coverage_data()
    except Exception as e:  # noqa: BLE001
        print(f"\n❌ FATAL ERROR: {e}")
