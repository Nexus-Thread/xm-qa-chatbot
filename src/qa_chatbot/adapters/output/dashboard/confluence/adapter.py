"""Confluence-ready dashboard artifact generator."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from html import escape
from typing import TYPE_CHECKING
from uuid import uuid4

from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.application.ports import DashboardPort

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.application.dtos import MonthlyReport, ProjectDetailDashboardData, TrendsDashboardData
    from qa_chatbot.application.ports import GenerateMonthlyReportPort, GetDashboardDataPort
    from qa_chatbot.domain import ProjectId, TimeWindow

LOGGER = logging.getLogger(__name__)

SMOKE_CHECK_MARKERS_BY_FILE: dict[str, tuple[str, ...]] = {
    "overview.confluence.html": (
        "<ac:structured-macro",
        "<ac:rich-text-body>",
        "Monthly QA Summary",
        "Section A — Quality Metrics",
        "Section B — Test Coverage",
        "</ac:rich-text-body></ac:structured-macro>",
        "<table",
        "</table>",
    ),
    "trends.confluence.html": (
        "<h1>Trends</h1>",
        "<p>Months:",
        "<table",
        "</table>",
    ),
}
PROJECT_DETAIL_FILE_PREFIX = "project-"


@dataclass
class ConfluenceDashboardAdapter(DashboardPort):
    """Generate Confluence-ready dashboard files locally."""

    get_dashboard_data_use_case: GetDashboardDataPort
    generate_monthly_report_use_case: GenerateMonthlyReportPort
    output_dir: Path

    def __post_init__(self) -> None:
        """Prepare output folder and data providers."""
        self._output_dir = self.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._use_case = self.get_dashboard_data_use_case
        self._report_use_case = self.generate_monthly_report_use_case

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview artifact."""
        report = self._report_use_case.execute(month)
        rendered = self._render_overview(report)
        return self._write_page("overview.confluence.html", rendered)

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Generate the project detail artifact."""
        data = self._use_case.build_project_detail(project_id, months)
        rendered = self._render_project_detail(data)
        return self._write_page(f"project-{project_id.value.lower()}.confluence.html", rendered)

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Generate the trends artifact."""
        data = self._use_case.build_trends(projects, months)
        rendered = self._render_trends(data)
        return self._write_page("trends.confluence.html", rendered)

    def _write_page(self, file_name: str, rendered: str) -> Path:
        self._smoke_check(rendered, file_name)
        output_path = self._output_dir / file_name
        temp_path = output_path.with_name(f".{output_path.name}.{uuid4().hex}.tmp")
        try:
            temp_path.write_text(rendered, encoding="utf-8")
            temp_path.replace(output_path)
        except OSError as err:
            temp_path.unlink(missing_ok=True)
            LOGGER.exception(
                "Confluence dashboard write failed",
                extra={
                    "component": self.__class__.__name__,
                    "file_name": file_name,
                    "output_path": str(output_path),
                    "error_type": type(err).__name__,
                },
            )
            msg = f"Failed to write Confluence dashboard output: {output_path}"
            raise DashboardRenderError(msg) from err
        LOGGER.info(
            "Confluence dashboard generated",
            extra={
                "component": self.__class__.__name__,
                "file_name": file_name,
                "output_path": str(output_path),
            },
        )
        return output_path

    def _render_overview(self, report: MonthlyReport) -> str:
        quality_rows = "".join(
            "<tr>"
            f"<td>{self._escape_text(row.business_stream)}</td>"
            f"<td>{self._escape_text(row.project_name)}</td>"
            f"<td>{self._escape_text(self._fmt(row.supported_releases_count))}</td>"
            f"<td>{self._escape_text(self._fmt(row.bugs_found.p1_p2))}</td>"
            f"<td>{self._escape_text(self._fmt(row.production_incidents.p1_p2))}</td>"
            f"<td>{self._escape_text(self._fmt(row.defect_leakage.rate_percent))}</td>"
            "</tr>"
            for row in report.quality_metrics_rows
        )
        coverage_rows = "".join(
            "<tr>"
            f"<td>{self._escape_text(row.business_stream)}</td>"
            f"<td>{self._escape_text(row.project_name)}</td>"
            f"<td>{self._escape_text(self._fmt(row.percentage_automation))}</td>"
            f"<td>{self._escape_text(self._fmt(row.manual_total))}</td>"
            f"<td>{self._escape_text(self._fmt(row.automated_total))}</td>"
            "</tr>"
            for row in report.test_coverage_rows
        )
        return (
            '<ac:structured-macro ac:name="info"><ac:rich-text-body>'
            f"<h1>Monthly QA Summary — {self._escape_text(report.metadata.reporting_period)}</h1>"
            f"<p>Completeness: {self._escape_text(report.completeness.status)}</p>"
            "<h2>Section A — Quality Metrics</h2>"
            "<table><tbody>"
            "<tr><th>Stream</th><th>Project</th><th>Supported Releases</th><th>Bugs P1-P2</th>"
            "<th>Incidents P1-P2</th><th>Defect Leakage %</th></tr>"
            f"{quality_rows}"
            "</tbody></table>"
            "<h2>Section B — Test Coverage</h2>"
            "<table><tbody>"
            "<tr><th>Stream</th><th>Project</th><th>Automation %</th><th>Manual</th><th>Automated</th></tr>"
            f"{coverage_rows}"
            "</tbody></table>"
            "</ac:rich-text-body></ac:structured-macro>"
        )

    def _render_project_detail(self, data: ProjectDetailDashboardData) -> str:
        rows = "".join(
            "<tr>"
            f"<td>{self._escape_text(snapshot.month.to_iso_month())}</td>"
            f"<td>{self._escape_text(self._fmt(snapshot.qa_metrics.get('manual_total')))}</td>"
            f"<td>{self._escape_text(self._fmt(snapshot.qa_metrics.get('automated_total')))}</td>"
            f"<td>{self._escape_text(self._fmt(snapshot.qa_metrics.get('percentage_automation')))}</td>"
            "</tr>"
            for snapshot in data.snapshots
        )
        return (
            f"<h1>Project Detail — {self._escape_text(data.project_id.value)}</h1>"
            "<table><tbody>"
            "<tr><th>Month</th><th>Manual</th><th>Automated</th><th>Automation %</th></tr>"
            f"{rows}"
            "</tbody></table>"
        )

    def _render_trends(self, data: TrendsDashboardData) -> str:
        months = ", ".join(self._escape_text(month.to_iso_month()) for month in data.months)
        sections = []
        for metric_name, series_list in data.qa_metric_series.items():
            series_rows = "".join(
                "<tr>"
                f"<td>{self._escape_text(series.label)}</td>"
                f"<td>{', '.join(self._escape_text(self._fmt(value)) for value in series.values)}</td>"
                "</tr>"
                for series in series_list
            )
            sections.append(
                "<h2>"
                f"{self._escape_text(metric_name)}"
                "</h2>"
                "<table><tbody><tr><th>Project</th><th>Values</th></tr>"
                f"{series_rows}"
                "</tbody></table>"
            )
        return f"<h1>Trends</h1><p>Months: {months}</p>{''.join(sections)}"

    @staticmethod
    def _fmt(value: float | str | None) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def _escape_text(value: str) -> str:
        return escape(value, quote=True)

    def _smoke_check(self, rendered: str, file_name: str) -> None:
        """Ensure rendered Confluence content includes expected markers."""
        markers = list(SMOKE_CHECK_MARKERS_BY_FILE.get(file_name, ("<h1>", "<table", "</table>")))
        if file_name.startswith(PROJECT_DETAIL_FILE_PREFIX):
            markers.extend(("<h1>Project Detail —", "<table", "</table>"))
        missing = [marker for marker in markers if marker not in rendered]
        if missing:
            LOGGER.error(
                "Confluence dashboard smoke check failed",
                extra={
                    "component": self.__class__.__name__,
                    "file_name": file_name,
                    "missing_markers": tuple(missing),
                },
            )
            missing_text = ", ".join(repr(marker) for marker in missing)
            message = f"Confluence dashboard render failed smoke check for {file_name}. Missing markers: {missing_text}"
            raise DashboardRenderError(message)
