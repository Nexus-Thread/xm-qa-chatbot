"""Snapshot tests for HTML dashboard generation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.adapters.output.dashboard.html import HtmlDashboardAdapter
from qa_chatbot.adapters.output.jira_mock import MockJiraAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
from qa_chatbot.application.dtos import CompletenessStatus, MonthlyReport, ReportMetadata
from qa_chatbot.application.dtos import TestCoverageRow as CoverageRowDTO
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry

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
    project_a = ProjectId("project-a")
    project_b = ProjectId("project-b")
    jan = TimeWindow.from_year_month(2026, 1)
    feb = TimeWindow.from_year_month(2026, 2)

    submission_a_jan = Submission.create(
        project_id=project_a,
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
        project_id=project_b,
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
        project_id=project_a,
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
    registry = build_default_stream_project_registry()
    jira_adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
    )
    report_use_case = GenerateMonthlyReportUseCase(
        storage_port=sqlite_adapter,
        jira_port=jira_adapter,
        registry=registry,
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
        now_provider=lambda: datetime(2026, 2, 4, 12, 0, 0, tzinfo=UTC),
    )
    dashboard_data_use_case = GetDashboardDataUseCase(storage_port=sqlite_adapter)
    return HtmlDashboardAdapter(
        get_dashboard_data_use_case=dashboard_data_use_case,
        generate_monthly_report_use_case=report_use_case,
        output_dir=tmp_path / "dashboards",
    )


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


def test_generate_overview_uses_reporting_month_coverage_fields(
    dashboard_adapter: HtmlDashboardAdapter,
    time_window_feb: TimeWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Render reporting-month test coverage values in overview columns."""

    class _StubReportUseCase:
        def __init__(self, fixed_report: MonthlyReport) -> None:
            self._fixed_report = fixed_report

        def execute(self, _month: TimeWindow) -> MonthlyReport:
            return self._fixed_report

    report = MonthlyReport(
        metadata=ReportMetadata(
            reporting_period="2026-02",
            generated_at="2026-02-04T12:00:00+00:00",
        ),
        completeness=CompletenessStatus(status="COMPLETE", missing=(), missing_by_project=None),
        quality_metrics_rows=(),
        test_coverage_rows=(
            CoverageRowDTO(
                business_stream="Client Engagement",
                project_name="Project A",
                percentage_automation=40.0,
                manual_total=120,
                manual_created_in_reporting_month=11,
                manual_updated_in_reporting_month=7,
                automated_total=80,
                automated_created_in_reporting_month=9,
                automated_updated_in_reporting_month=4,
            ),
        ),
        overall_test_cases=200,
    )
    monkeypatch.setattr(dashboard_adapter, "_report_use_case", _StubReportUseCase(report))

    output_path = dashboard_adapter.generate_overview(time_window_feb)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))

    assert ">11</td>" in html
    assert ">7</td>" in html
    assert ">9</td>" in html
    assert ">4</td>" in html


def test_generate_overview_wraps_template_load_errors(
    dashboard_adapter: HtmlDashboardAdapter,
    time_window_feb: TimeWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap template loading failures with DashboardRenderError."""

    def _raise_load_error(_template_name: str) -> None:
        raise RuntimeError

    environment = dashboard_adapter._environment  # noqa: SLF001
    monkeypatch.setattr(environment, "get_template", _raise_load_error)

    with pytest.raises(DashboardRenderError, match=r"Failed to load dashboard template: overview\.html") as exc_info:
        dashboard_adapter.generate_overview(time_window_feb)

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_generate_overview_wraps_template_render_errors(
    dashboard_adapter: HtmlDashboardAdapter,
    time_window_feb: TimeWindow,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap template rendering failures with DashboardRenderError."""

    class _BrokenTemplate:
        def render(self, **_context: object) -> str:
            raise RuntimeError

    environment = dashboard_adapter._environment  # noqa: SLF001
    monkeypatch.setattr(environment, "get_template", lambda _template_name: _BrokenTemplate())

    with pytest.raises(DashboardRenderError, match=r"Failed to render dashboard template: overview\.html") as exc_info:
        dashboard_adapter.generate_overview(time_window_feb)

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_write_atomic_wraps_write_errors(
    dashboard_adapter: HtmlDashboardAdapter,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Wrap file write failures with DashboardRenderError."""

    def _raise_write_error(_self: Path, _content: str, *, encoding: str = "utf-8") -> int:
        del encoding
        raise OSError

    monkeypatch.setattr(Path, "write_text", _raise_write_error)

    with pytest.raises(DashboardRenderError, match="Failed to write dashboard output:") as exc_info:
        dashboard_adapter._write_atomic(tmp_path / "overview.html", "test")  # noqa: SLF001

    assert isinstance(exc_info.value.__cause__, OSError)


def test_generate_project_detail_snapshot(
    dashboard_adapter: HtmlDashboardAdapter,
    project_id_a: ProjectId,
    request: pytest.FixtureRequest,
) -> None:
    """Render and snapshot the project detail dashboard."""
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    output_path = dashboard_adapter.generate_project_detail(project_id_a, months)
    html = _normalize_html(output_path.read_text(encoding="utf-8"))
    _assert_snapshot(request, "project_detail", html)


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
