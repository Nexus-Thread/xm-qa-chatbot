"""Seed the database with pseudo-random test coverage data for all projects."""

from __future__ import annotations

import random
from datetime import UTC, datetime
from pathlib import Path

from qa_chatbot.adapters.input import EnvSettingsAdapter
from qa_chatbot.adapters.output import HtmlDashboardAdapter, InMemoryMetricsAdapter, MockJiraAdapter, SQLiteAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry

# ruff: noqa: T201


def load_active_projects() -> list[dict[str, str]]:
    """Load all active projects from the hardcoded registry."""
    registry = build_default_stream_project_registry()
    projects = [{"id": project.id, "name": project.name} for project in registry.active_projects()]
    print(f"✅ Loaded {len(projects)} active projects\n")
    return projects


def generate_baseline_data() -> dict[str, int]:
    """Generate random baseline test coverage data."""
    manual_total = random.randint(100, 2000)  # noqa: S311
    automated_total = random.randint(50, 1500)  # noqa: S311

    # Created/Updated: 5-15% of totals with some variation
    manual_activity_rate = random.uniform(0.05, 0.15)  # noqa: S311
    automated_activity_rate = random.uniform(0.05, 0.15)  # noqa: S311

    return {
        "manual_total": manual_total,
        "automated_total": automated_total,
        "manual_created": int(manual_total * manual_activity_rate * random.uniform(0.4, 0.7)),  # noqa: S311
        "manual_updated": int(manual_total * manual_activity_rate * random.uniform(0.3, 0.6)),  # noqa: S311
        "automated_created": int(automated_total * automated_activity_rate * random.uniform(0.4, 0.7)),  # noqa: S311
        "automated_updated": int(automated_total * automated_activity_rate * random.uniform(0.3, 0.6)),  # noqa: S311
    }


def apply_trend(
    previous: dict[str, int],
    trend_direction: str,
) -> dict[str, int]:
    """Apply trend to previous month's data (3-15% growth or 3-10% decline)."""
    trend_factor = random.uniform(1.03, 1.15) if trend_direction == "increasing" else random.uniform(0.9, 0.97)  # noqa: S311

    # Add random noise
    noise = random.uniform(0.98, 1.02)  # noqa: S311
    final_factor = trend_factor * noise

    # Apply to all fields
    result = {}
    for key, value in previous.items():
        new_value = int(value * final_factor)
        result[key] = max(0, new_value)  # Ensure non-negative

    return result


def calculate_automation_percentage(manual: int, automated: int) -> float:
    """Calculate automation percentage from totals."""
    total = manual + automated
    if total == 0:
        return 0.0
    return round((automated / total) * 100, 2)


def create_test_coverage_metrics(data: dict[str, int]) -> TestCoverageMetrics:
    """Create TestCoverageMetrics from data dict."""
    percentage = calculate_automation_percentage(
        data["manual_total"],
        data["automated_total"],
    )

    return TestCoverageMetrics(
        manual_total=data["manual_total"],
        automated_total=data["automated_total"],
        manual_created_in_reporting_month=data["manual_created"],
        manual_updated_in_reporting_month=data["manual_updated"],
        automated_created_in_reporting_month=data["automated_created"],
        automated_updated_in_reporting_month=data["automated_updated"],
        percentage_automation=percentage,
    )


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


def _seed_project_data(
    project_config: dict[str, str],
    time_windows: list[TimeWindow],
    submitter: SubmitProjectDataUseCase,
) -> int:
    project_id_str = project_config["id"]
    project_name = project_config["name"]
    project_id = ProjectId.from_raw(project_id_str)

    trend_direction = random.choice(["increasing", "decreasing"])  # noqa: S311
    trend_emoji = "📈" if trend_direction == "increasing" else "📉"

    print(f"\n{trend_emoji} {project_name} ({project_id_str}) - {trend_direction}")

    data_month1 = generate_baseline_data()
    data_month2 = apply_trend(data_month1, trend_direction)
    data_month3 = apply_trend(data_month2, trend_direction)
    all_month_data = [data_month1, data_month2, data_month3]

    submissions_count = 0
    for time_window, data in zip(time_windows, all_month_data, strict=True):
        test_coverage = create_test_coverage_metrics(data)

        command = SubmissionCommand(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=test_coverage,
                overall_test_cases=None,
                supported_releases_count=None,
            ),
            raw_conversation="Seeded data via seed_database.py script",
            created_at=datetime.now(UTC),
        )

        submitter.execute(command)
        submissions_count += 1

        print(
            f"  {time_window.to_iso_month()}: "
            f"M={data['manual_total']:4d}, "
            f"A={data['automated_total']:4d}, "
            f"Auto%={test_coverage.percentage_automation:5.2f}%"
        )

    return submissions_count


def seed_database() -> None:
    """Seed the database with pseudo-random data."""
    settings = EnvSettingsAdapter().load()

    print("=" * 80)
    print("DATABASE SEEDING SCRIPT")
    print("=" * 80)
    print("\nGenerating pseudo-random test coverage data for:")
    print("  - All active projects")
    print("  - Months: 2025-11, 2025-12, 2026-01")
    print("  - Random increasing/decreasing trends")
    print("=" * 80 + "\n")

    # Initialize adapters
    print("Step 1: Initializing adapters...")
    storage = SQLiteAdapter(
        database_url=settings.database_url,
        echo=settings.database_echo,
        timeout_seconds=settings.database_timeout_seconds,
    )
    storage.initialize_schema()
    dashboard_adapter = _build_dashboard_adapter(settings=settings, storage=storage)

    metrics_adapter = InMemoryMetricsAdapter()
    print("✅ Adapters initialized\n")

    # Clear existing data
    print("Step 2: Clearing existing submissions...")
    storage.clear_all_submissions()
    print("✅ Database cleared\n")

    # Load projects
    print("Step 3: Loading active projects...")
    projects = load_active_projects()

    # Create use case
    submitter = SubmitProjectDataUseCase(
        storage_port=storage,
        dashboard_port=dashboard_adapter,
        metrics_port=metrics_adapter,
    )

    # Define time windows
    time_windows = [
        TimeWindow.from_year_month(2025, 11),
        TimeWindow.from_year_month(2025, 12),
        TimeWindow.from_year_month(2026, 1),
    ]

    # Seed data
    print("Step 4: Generating and submitting data...")
    total_submissions = 0

    for project_config in projects:
        total_submissions += _seed_project_data(
            project_config=project_config,
            time_windows=time_windows,
            submitter=submitter,
        )

    print("\n" + "=" * 80)
    print(f"✅ SUCCESS: Seeded {total_submissions} submissions for {len(projects)} projects")
    print("=" * 80)
    print("\nNext steps:")
    print("  1. View the dashboard: python scripts/serve_dashboard.py")
    print("  2. Check the database: sqlite3 qa_chatbot.db")
    print("  3. Query submissions: SELECT project_id, month, created_at FROM submissions;")
    print()


if __name__ == "__main__":
    # Set random seed for reproducibility (optional - comment out for true randomness)
    random.seed(42)

    try:
        seed_database()
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}")
        import traceback

        traceback.print_exc()
        raise
