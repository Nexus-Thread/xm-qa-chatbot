"""Focused unit tests for the Confluence dashboard adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import pytest

from qa_chatbot.adapters.output.dashboard.confluence import ConfluenceDashboardAdapter
from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.application.dtos import (
    BucketCountDTO,
    CompletenessStatus,
    DefectLeakageDTO,
    MonthlyReport,
    ProjectDetailDashboardData,
    ProjectMonthlySnapshot,
    QualityMetricsRow,
    ReportMetadata,
    TrendsDashboardData,
    TrendSeries,
)
from qa_chatbot.application.dtos import (
    TestCoverageRow as CoverageRowDTO,
)
from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass(frozen=True)
class StubReportUseCase:
    """Return a fixed monthly report."""

    report: MonthlyReport

    def execute(self, _month: TimeWindow) -> MonthlyReport:
        """Return the configured report."""
        return self.report


@dataclass(frozen=True)
class StubDashboardDataUseCase:
    """Return fixed dashboard DTO payloads."""

    project_detail_data: ProjectDetailDashboardData
    trends_data: TrendsDashboardData

    def build_project_detail(self, _project_id: ProjectId, _months: list[TimeWindow]) -> ProjectDetailDashboardData:
        """Return the configured project detail data."""
        return self.project_detail_data

    def build_trends(self, _projects: list[ProjectId], _months: list[TimeWindow]) -> TrendsDashboardData:
        """Return the configured trends data."""
        return self.trends_data


def _default_report() -> MonthlyReport:
    return MonthlyReport(
        metadata=ReportMetadata(
            reporting_period="2026-02",
            generated_at="2026-02-04T12:00:00+00:00",
        ),
        completeness=CompletenessStatus(status="COMPLETE", missing=(), missing_by_project=None),
        quality_metrics_rows=(
            QualityMetricsRow(
                business_stream="Client Engagement",
                project_name="Project A",
                supported_releases_count=2,
                bugs_found=BucketCountDTO(p1_p2=1, p3_p4=0),
                production_incidents=BucketCountDTO(p1_p2=0, p3_p4=0),
                defect_leakage=DefectLeakageDTO(numerator=1, denominator=20, rate_percent=5.0),
            ),
        ),
        test_coverage_rows=(
            CoverageRowDTO(
                business_stream="Client Engagement",
                project_name="Project A",
                percentage_automation=40.0,
                manual_total=120,
                manual_created_in_reporting_month=10,
                manual_updated_in_reporting_month=5,
                automated_total=80,
                automated_created_in_reporting_month=8,
                automated_updated_in_reporting_month=3,
            ),
        ),
        overall_test_cases=200,
    )


def _default_project_detail_data() -> ProjectDetailDashboardData:
    return ProjectDetailDashboardData(
        project_id=ProjectId("project-a"),
        snapshots=[
            ProjectMonthlySnapshot(
                month=TimeWindow.from_year_month(2026, 2),
                qa_metrics={
                    "manual_total": 120,
                    "automated_total": 80,
                    "percentage_automation": 40.0,
                },
                project_status={},
                daily_update={},
            )
        ],
    )


def _default_trends_data() -> TrendsDashboardData:
    return TrendsDashboardData(
        projects=[ProjectId("project-a")],
        months=[TimeWindow.from_year_month(2026, 2)],
        qa_metric_series={
            "manual_total": [
                TrendSeries(label="project-a", values=[120]),
            ]
        },
        project_metric_series={},
    )


def _build_adapter(
    tmp_path: Path,
    *,
    report: MonthlyReport | None = None,
    project_detail_data: ProjectDetailDashboardData | None = None,
    trends_data: TrendsDashboardData | None = None,
) -> ConfluenceDashboardAdapter:
    return ConfluenceDashboardAdapter(
        get_dashboard_data_use_case=cast(
            "Any",
            StubDashboardDataUseCase(
                project_detail_data=project_detail_data or _default_project_detail_data(),
                trends_data=trends_data or _default_trends_data(),
            ),
        ),
        generate_monthly_report_use_case=cast(
            "Any",
            StubReportUseCase(report=report or _default_report()),
        ),
        output_dir=tmp_path / "dashboards",
    )


def test_generate_overview_escapes_dynamic_values(tmp_path: Path) -> None:
    """Escape dynamic values in generated overview markup."""
    report = MonthlyReport(
        metadata=ReportMetadata(
            reporting_period="2026-02 & <b>",
            generated_at="2026-02-04T12:00:00+00:00",
        ),
        completeness=CompletenessStatus(status="PARTIAL <check>", missing=(), missing_by_project=None),
        quality_metrics_rows=(
            QualityMetricsRow(
                business_stream="Core <Ops>",
                project_name='Project "A" & friends',
                supported_releases_count=2,
                bugs_found=BucketCountDTO(p1_p2=1, p3_p4=0),
                production_incidents=BucketCountDTO(p1_p2=0, p3_p4=0),
                defect_leakage=DefectLeakageDTO(numerator=1, denominator=20, rate_percent=5.0),
            ),
        ),
        test_coverage_rows=(
            CoverageRowDTO(
                business_stream="Core <Ops>",
                project_name='Project "A" & friends',
                percentage_automation=40.0,
                manual_total=120,
                manual_created_in_reporting_month=10,
                manual_updated_in_reporting_month=5,
                automated_total=80,
                automated_created_in_reporting_month=8,
                automated_updated_in_reporting_month=3,
            ),
        ),
        overall_test_cases=200,
    )
    adapter = _build_adapter(tmp_path, report=report)

    path = adapter.generate_overview(TimeWindow.from_year_month(2026, 2))
    content = path.read_text(encoding="utf-8")

    assert "Monthly QA Summary — 2026-02 &amp; &lt;b&gt;" in content
    assert "Completeness: PARTIAL &lt;check&gt;" in content
    assert "<td>Core &lt;Ops&gt;</td>" in content
    assert "<td>Project &quot;A&quot; &amp; friends</td>" in content
    assert "PARTIAL <check>" not in content


def test_generate_trends_escapes_metric_and_series_labels(tmp_path: Path) -> None:
    """Escape trends metric names and project labels in generated markup."""
    trends_data = TrendsDashboardData(
        projects=[ProjectId("project-a")],
        months=[TimeWindow.from_year_month(2026, 2)],
        qa_metric_series={
            "manual_<total>": [
                TrendSeries(label='project & "A"', values=[120]),
            ]
        },
        project_metric_series={},
    )
    adapter = _build_adapter(tmp_path, trends_data=trends_data)

    path = adapter.generate_trends([ProjectId("project-a")], [TimeWindow.from_year_month(2026, 2)])
    content = path.read_text(encoding="utf-8")

    assert "<h2>manual_&lt;total&gt;</h2>" in content
    assert "<td>project &amp;" in content
    assert "&quot;A&quot;" in content


def test_write_page_wraps_file_write_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap filesystem write failures as dashboard render errors."""
    adapter = _build_adapter(tmp_path)

    def _raise_write_error(_self: Path, _content: str, *, encoding: str = "utf-8") -> int:
        del encoding
        message = "disk is full"
        raise OSError(message)

    monkeypatch.setattr(Path, "write_text", _raise_write_error)

    with pytest.raises(DashboardRenderError, match="Failed to write Confluence dashboard output") as exc_info:
        adapter.generate_overview(TimeWindow.from_year_month(2026, 2))

    assert isinstance(exc_info.value.__cause__, OSError)


def test_write_page_uses_unique_temp_file_name(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use a unique temp file path for atomic output writes."""
    adapter = _build_adapter(tmp_path)
    observed: dict[str, object] = {}

    def _capture_write(self: Path, _content: str, *, encoding: str = "utf-8") -> int:
        del encoding
        observed["temp_path"] = self
        return len(_content)

    def _capture_replace(_self: Path, target: Path) -> Path:
        observed["replace_target"] = target
        return target

    monkeypatch.setattr(Path, "write_text", _capture_write)
    monkeypatch.setattr(Path, "replace", _capture_replace)

    output_path = adapter.generate_overview(TimeWindow.from_year_month(2026, 2))

    temp_path = observed["temp_path"]
    assert isinstance(temp_path, Path)
    assert temp_path.parent == output_path.parent
    assert temp_path.name.startswith(".overview.confluence.html.")
    assert temp_path.name.endswith(".tmp")
    uuid_text = temp_path.name.removeprefix(".overview.confluence.html.").removesuffix(".tmp")
    UUID(uuid_text)
    assert observed["replace_target"] == output_path


def test_generate_overview_smoke_check_reports_missing_markers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Report detailed marker failures for malformed overview output."""
    adapter = _build_adapter(tmp_path)
    monkeypatch.setattr(adapter, "_render_overview", lambda _report: "<h1>Monthly QA Summary</h1>")

    with pytest.raises(DashboardRenderError, match=r"failed smoke check") as exc_info:
        adapter.generate_overview(TimeWindow.from_year_month(2026, 2))

    message = str(exc_info.value)
    assert "Missing markers:" in message
    assert "'<ac:structured-macro'" in message
    assert "'Section A — Quality Metrics'" in message
