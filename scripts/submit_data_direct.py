"""Submit test coverage data directly via use cases (bypassing Gradio UI)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from qa_chatbot.adapters.output import HtmlDashboardAdapter, InMemoryMetricsAdapter, SQLiteAdapter
from qa_chatbot.application import SubmitTeamDataUseCase
from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow

# ruff: noqa: T201, DTZ005


def submit_test_coverage_data() -> None:
    """Submit test coverage data directly through use cases."""
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
    storage = SQLiteAdapter(database_url="sqlite:///./qa_chatbot.db", echo=False)
    storage.initialize_schema()
    print("✅ Storage initialized\n")

    print("Step 2: Initializing dashboard adapter...")
    dashboard_output_dir = Path("./dashboard_html")
    dashboard_adapter = HtmlDashboardAdapter(storage_port=storage, output_dir=dashboard_output_dir)
    print("✅ Dashboard adapter initialized\n")

    print("Step 3: Initializing metrics adapter...")
    metrics_adapter = InMemoryMetricsAdapter()
    print("✅ Metrics adapter initialized\n")

    print("Step 4: Creating submission command...")
    # Create the submission command with test coverage data
    project_id = ProjectId.from_raw("client_trading")
    time_window = TimeWindow.from_year_month(2026, 1)

    test_coverage = TestCoverageMetrics(
        manual_total=1000,
        automated_total=500,
        manual_created_last_month=100,
        manual_updated_last_month=120,
        automated_created_last_month=50,
        automated_updated_last_month=30,
        percentage_automation=33.33,
    )

    command = SubmissionCommand(
        project_id=project_id,
        time_window=time_window,
        test_coverage=test_coverage,
        overall_test_cases=None,
        raw_conversation="Direct API submission via script",
        created_at=datetime.now(),
    )
    print("✅ Submission command created\n")

    print("Step 5: Submitting data...")
    submitter = SubmitTeamDataUseCase(
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
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        submit_test_coverage_data()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
