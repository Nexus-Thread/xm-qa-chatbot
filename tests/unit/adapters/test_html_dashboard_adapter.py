"""Snapshot tests for HTML dashboard generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.output.dashboard.html import HtmlDashboardAdapter
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow

if TYPE_CHECKING:
    from pathlib import Path

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
    team_a = ProjectId("project-a")
    team_b = ProjectId("project-b")
    jan = TimeWindow.from_year_month(2026, 1)
    feb = TimeWindow.from_year_month(2026, 2)

    submission_a_jan = Submission.create(
        project_id=team_a,
        month=jan,
        test_coverage=TestCoverageMetrics(
            manual_total=120,
            automated_total=80,
            manual_created_in_reporting_month=10,
            manual_updated_in_reporting_month=5,
            automated_created_in_reporting_month=8,
            automated_updated_in_reporting_month=3,
            percentage_automation=40.0,
        ),
        overall_test_cases=None,
    )
    submission_b_jan = Submission.create(
        project_id=team_b,
        month=jan,
        test_coverage=TestCoverageMetrics(
            manual_total=95,
            automated_total=70,
            manual_created_in_reporting_month=6,
            manual_updated_in_reporting_month=4,
            automated_created_in_reporting_month=5,
            automated_updated_in_reporting_month=2,
            percentage_automation=42.0,
        ),
        overall_test_cases=None,
    )
    submission_a_feb = Submission.create(
        project_id=team_a,
        month=feb,
        test_coverage=TestCoverageMetrics(
            manual_total=140,
            automated_total=100,
            manual_created_in_reporting_month=12,
            manual_updated_in_reporting_month=6,
            automated_created_in_reporting_month=9,
            automated_updated_in_reporting_month=4,
            percentage_automation=41.0,
        ),
        overall_test_cases=None,
    )

    sqlite_adapter.save_submission(submission_a_jan)
    sqlite_adapter.save_submission(submission_b_jan)
    sqlite_adapter.save_submission(submission_a_feb)


@pytest.fixture
def dashboard_adapter(sqlite_adapter: SQLiteAdapter, tmp_path: Path) -> HtmlDashboardAdapter:
    """Provide the HTML dashboard adapter with seeded data."""
    _seed_submissions(sqlite_adapter)
    adapter = HtmlDashboardAdapter(
        storage_port=sqlite_adapter,
        output_dir=tmp_path / "dashboards",
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
    )
    return _with_fixed_report_timestamp(adapter)


def _with_fixed_report_timestamp(adapter: HtmlDashboardAdapter) -> HtmlDashboardAdapter:
    report_use_case = adapter._report_use_case  # noqa: SLF001
    adapter._report_use_case = report_use_case.__class__(  # noqa: SLF001
        storage_port=report_use_case.storage_port,
        jira_port=report_use_case.jira_port,
        registry=report_use_case.registry,
        timezone=report_use_case.timezone,
        edge_case_policy=report_use_case.edge_case_policy,
        completeness_mode=report_use_case.completeness_mode,
        now_provider=lambda: datetime(2026, 2, 4, 12, 0, 0, tzinfo=UTC),
    )
    return adapter


def test_generate_overview_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    time_window_feb: TimeWindow,
) -> None:
    """Render overview dashboard with expected core sections."""
    output_path = dashboard_adapter.generate_overview(time_window_feb)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    assert "Monthly QA Summary" in html
    assert "Completeness: PARTIAL" in html
    assert "Section B — Test Coverage" in html


def test_generate_team_detail_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    project_id_a: ProjectId,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the team detail dashboard."""
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    output_path = dashboard_adapter.generate_team_detail(project_id_a, months)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "team_detail", html)


def test_generate_trends_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    project_id_a: ProjectId,
    project_id_b: ProjectId,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the trends dashboard."""
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    output_path = dashboard_adapter.generate_trends([project_id_a, project_id_b], months)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "trends", html)
