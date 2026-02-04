"""Snapshot tests for HTML dashboard generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.output.dashboard.html import HtmlDashboardAdapter
from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, Submission, TeamId, TimeWindow

if TYPE_CHECKING:
    from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter


@dataclass(frozen=True)
class SnapshotFile:
    """Snapshot file helper for HTML output."""

    path: Path

    def read(self) -> str:
        """Read snapshot contents from disk."""
        return self.path.read_text(encoding="utf-8")

    def write(self, content: str) -> None:
        """Write snapshot contents to disk."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(content, encoding="utf-8")


def _snapshot_path(request: pytest.FixtureRequest, name: str) -> Path:
    return request.path.parent / "snapshots" / f"{name}.html"


def _assert_snapshot(request: pytest.FixtureRequest, name: str, content: str) -> None:
    snapshot = SnapshotFile(_snapshot_path(request, name))
    if not snapshot.path.exists():
        snapshot.write(content)
        pytest.skip(f"Snapshot created at {snapshot.path}. Re-run the test to compare.")
    assert content == _normalize_html(snapshot.read())


def _normalize_html(content: str) -> str:
    normalized_lines = []
    for line in content.replace("\r\n", "\n").split("\n"):
        stripped = line.strip()
        if not stripped:
            continue
        normalized_lines.append(stripped)
    return "\n".join(normalized_lines)


def _seed_submissions(sqlite_adapter: SQLiteAdapter) -> None:
    team_a = TeamId("Team A")
    team_b = TeamId("Team B")
    jan = TimeWindow.from_year_month(2026, 1)
    feb = TimeWindow.from_year_month(2026, 2)

    submission_a_jan = Submission.create(
        team_id=team_a,
        month=jan,
        qa_metrics=QAMetrics(
            tests_passed=120,
            tests_failed=5,
            test_coverage_percent=87.5,
            bug_count=3,
            critical_bugs=1,
            deployment_ready=True,
        ),
        project_status=ProjectStatus(
            sprint_progress_percent=76.0,
            blockers=("Env flakiness",),
            milestones_completed=("Smoke suite",),
            risks=("API instability",),
        ),
        daily_update=DailyUpdate(
            completed_tasks=("Regression", "Load test"),
            planned_tasks=("Coverage audit",),
            capacity_hours=6.5,
            issues=("Staging latency",),
        ),
    )
    submission_b_jan = Submission.create(
        team_id=team_b,
        month=jan,
        qa_metrics=QAMetrics(
            tests_passed=95,
            tests_failed=12,
            test_coverage_percent=81.0,
            bug_count=6,
            critical_bugs=0,
            deployment_ready=False,
        ),
        project_status=ProjectStatus(
            sprint_progress_percent=61.0,
            blockers=(),
            milestones_completed=("Upgrade",),
            risks=("Data drift",),
        ),
        daily_update=DailyUpdate(
            completed_tasks=("Test plan",),
            planned_tasks=("Security scan",),
            capacity_hours=5.0,
            issues=(),
        ),
    )
    submission_a_feb = Submission.create(
        team_id=team_a,
        month=feb,
        qa_metrics=QAMetrics(
            tests_passed=140,
            tests_failed=2,
            test_coverage_percent=90.0,
            bug_count=2,
            critical_bugs=0,
            deployment_ready=True,
        ),
        project_status=ProjectStatus(
            sprint_progress_percent=82.0,
            blockers=("Vendor wait",),
            milestones_completed=("Scale test",),
            risks=(),
        ),
        daily_update=DailyUpdate(
            completed_tasks=("Release candidate",),
            planned_tasks=("Postmortem",),
            capacity_hours=7.0,
            issues=("Deployment queue",),
        ),
    )

    sqlite_adapter.save_submission(submission_a_jan)
    sqlite_adapter.save_submission(submission_b_jan)
    sqlite_adapter.save_submission(submission_a_feb)


@pytest.fixture
def dashboard_adapter(sqlite_adapter: SQLiteAdapter, tmp_path: Path) -> HtmlDashboardAdapter:
    """Provide the HTML dashboard adapter with seeded data."""
    _seed_submissions(sqlite_adapter)
    return HtmlDashboardAdapter(storage_port=sqlite_adapter, output_dir=tmp_path / "dashboards")


def test_generate_overview_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    time_window_feb: TimeWindow,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the overview dashboard."""
    output_path = dashboard_adapter.generate_overview(time_window_feb)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "overview", html)


def test_generate_team_detail_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    team_id_a: TeamId,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the team detail dashboard."""
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    output_path = dashboard_adapter.generate_team_detail(team_id_a, months)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "team_detail", html)


def test_generate_trends_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    team_id_a: TeamId,
    team_id_b: TeamId,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the trends dashboard."""
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    output_path = dashboard_adapter.generate_trends([team_id_a, team_id_b], months)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "trends", html)
