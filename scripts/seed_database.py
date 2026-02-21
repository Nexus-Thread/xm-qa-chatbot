"""Seed the database with pseudo-random test coverage data for all projects."""

from __future__ import annotations

import hashlib
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import TypeVar

from qa_chatbot.adapters.input import EnvSettingsAdapter
from qa_chatbot.adapters.output import HtmlDashboardAdapter, InMemoryMetricsAdapter, MockJiraAdapter, SQLiteAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry

T = TypeVar("T")


class DeterministicRng:
    """Deterministic pseudo-random generator based on SHA-256."""

    def __init__(self, seed: str) -> None:
        """Initialize generator state with a stable seed."""
        self._seed = seed
        self._counter = 0

    def _next_fraction(self) -> float:
        payload = f"{self._seed}:{self._counter}".encode()
        self._counter += 1
        digest = hashlib.sha256(payload).digest()
        value = int.from_bytes(digest[:8], byteorder="big", signed=False)
        return value / float((1 << 64) - 1)

    def randint(self, start: int, end: int) -> int:
        """Return deterministic integer in inclusive range."""
        if start > end:
            msg = "start must be <= end"
            raise ValueError(msg)
        span = end - start + 1
        offset = min(span - 1, int(self._next_fraction() * span))
        return start + offset

    def uniform(self, start: float, end: float) -> float:
        """Return deterministic float in range."""
        if start > end:
            msg = "start must be <= end"
            raise ValueError(msg)
        return start + (end - start) * self._next_fraction()

    def choice(self, items: list[T]) -> T:
        """Return deterministic item from a non-empty list."""
        if not items:
            msg = "items must not be empty"
            raise ValueError(msg)
        index = min(len(items) - 1, int(self._next_fraction() * len(items)))
        return items[index]


def _echo(message: str = "") -> None:
    """Write a user-facing message to stdout."""
    sys.stdout.write(f"{message}\n")


def load_active_projects() -> list[dict[str, str]]:
    """Load all active projects from the hardcoded registry."""
    registry = build_default_stream_project_registry()
    projects = [{"id": project.id, "name": project.name} for project in registry.active_projects()]
    _echo(f"✅ Loaded {len(projects)} active projects\n")
    return projects


def generate_baseline_data(rng: DeterministicRng) -> dict[str, int]:
    """Generate random baseline test coverage data."""
    manual_total = rng.randint(100, 2000)
    automated_total = rng.randint(50, 1500)

    # Created/Updated: 5-15% of totals with some variation
    manual_activity_rate = rng.uniform(0.05, 0.15)
    automated_activity_rate = rng.uniform(0.05, 0.15)

    return {
        "manual_total": manual_total,
        "automated_total": automated_total,
        "manual_created": int(manual_total * manual_activity_rate * rng.uniform(0.4, 0.7)),
        "manual_updated": int(manual_total * manual_activity_rate * rng.uniform(0.3, 0.6)),
        "automated_created": int(automated_total * automated_activity_rate * rng.uniform(0.4, 0.7)),
        "automated_updated": int(automated_total * automated_activity_rate * rng.uniform(0.3, 0.6)),
    }


def apply_trend(
    previous: dict[str, int],
    trend_direction: str,
    rng: DeterministicRng,
) -> dict[str, int]:
    """Apply trend to previous month's data (3-15% growth or 3-10% decline)."""
    trend_factor = rng.uniform(1.03, 1.15) if trend_direction == "increasing" else rng.uniform(0.9, 0.97)

    # Add random noise
    noise = rng.uniform(0.98, 1.02)
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
    rng: DeterministicRng,
) -> tuple[int, int]:
    project_id_str = project_config["id"]
    project_name = project_config["name"]
    project_id = ProjectId.from_raw(project_id_str)

    trend_direction = rng.choice(["increasing", "decreasing"])
    trend_emoji = "📈" if trend_direction == "increasing" else "📉"

    _echo(f"\n{trend_emoji} {project_name} ({project_id_str}) - {trend_direction}")

    data_month1 = generate_baseline_data(rng)
    data_month2 = apply_trend(data_month1, trend_direction, rng)
    data_month3 = apply_trend(data_month2, trend_direction, rng)
    all_month_data = [data_month1, data_month2, data_month3]

    submissions_count = 0
    warnings_count = 0
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

        result = submitter.execute(command)
        submissions_count += 1
        warnings_count += len(result.warnings)

        if result.has_warnings:
            _echo(f"  ⚠️  Dashboard warnings for {time_window.to_iso_month()}:")
            for warning in result.warnings:
                _echo(f"     - {warning}")

        _echo(
            f"  {time_window.to_iso_month()}: "
            f"M={data['manual_total']:4d}, "
            f"A={data['automated_total']:4d}, "
            f"Auto%={test_coverage.percentage_automation:5.2f}%"
        )

    return submissions_count, warnings_count


def seed_database() -> None:
    """Seed the database with pseudo-random data."""
    settings = EnvSettingsAdapter().load()

    _echo("=" * 80)
    _echo("DATABASE SEEDING SCRIPT")
    _echo("=" * 80)
    _echo("\nGenerating pseudo-random test coverage data for:")
    _echo("  - All active projects")
    _echo("  - Months: 2025-11, 2025-12, 2026-01")
    _echo("  - Random increasing/decreasing trends")
    _echo("=" * 80 + "\n")

    # Initialize adapters
    _echo("Step 1: Initializing adapters...")
    storage = SQLiteAdapter(
        database_url=settings.database_url,
        echo=settings.database_echo,
        timeout_seconds=settings.database_timeout_seconds,
    )
    storage.initialize_schema()
    dashboard_adapter = _build_dashboard_adapter(settings=settings, storage=storage)

    metrics_adapter = InMemoryMetricsAdapter()
    _echo("✅ Adapters initialized\n")

    # Clear existing data
    _echo("Step 2: Clearing existing submissions...")
    storage.clear_all_submissions()
    _echo("✅ Database cleared\n")

    # Load projects
    _echo("Step 3: Loading active projects...")
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
    _echo("Step 4: Generating and submitting data...")
    total_submissions = 0
    total_warnings = 0
    rng = DeterministicRng(seed="xm-qa-seed-42")

    for project_config in projects:
        project_submissions, project_warnings = _seed_project_data(
            project_config=project_config,
            time_windows=time_windows,
            submitter=submitter,
            rng=rng,
        )
        total_submissions += project_submissions
        total_warnings += project_warnings

    _echo("\n" + "=" * 80)
    _echo(f"✅ SUCCESS: Seeded {total_submissions} submissions for {len(projects)} projects")
    if total_warnings:
        _echo(f"⚠️  Dashboard warnings encountered: {total_warnings}")
    _echo("=" * 80)
    _echo("\nNext steps:")
    _echo("  1. View the dashboard: python scripts/serve_dashboard.py")
    _echo("  2. Check the database: sqlite3 qa_chatbot.db")
    _echo("  3. Query submissions: SELECT project_id, month, created_at FROM submissions;")
    _echo()


if __name__ == "__main__":
    seed_database()
