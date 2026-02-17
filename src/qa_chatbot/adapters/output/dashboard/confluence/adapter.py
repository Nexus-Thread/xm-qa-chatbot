"""Confluence-ready dashboard artifact generator."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.adapters.output.jira_mock import MockJiraAdapter
from qa_chatbot.application.ports import DashboardPort, StoragePort
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.application.use_cases import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
from qa_chatbot.domain import build_default_stream_project_registry

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.application.dtos import MonthlyReport, ProjectDetailDashboardData, TrendsDashboardData
    from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass
class ConfluenceDashboardAdapter(DashboardPort):
    """Generate Confluence-ready dashboard files locally."""

    storage_port: StoragePort
    output_dir: Path
    jira_base_url: str
    jira_username: str
    jira_api_token: str
    report_timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Prepare output folder and data providers."""
        self._output_dir = self.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._use_case = GetDashboardDataUseCase(self.storage_port)
        registry = build_default_stream_project_registry()
        edge_case_policy = EdgeCasePolicy()
        self._report_use_case = GenerateMonthlyReportUseCase(
            storage_port=self.storage_port,
            jira_port=MockJiraAdapter(
                registry=registry,
                jira_base_url=self.jira_base_url,
                jira_username=self.jira_username,
                jira_api_token=self.jira_api_token,
            ),
            registry=registry,
            timezone=self.report_timezone,
            edge_case_policy=edge_case_policy,
        )

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
        temp_path = output_path.with_suffix(output_path.suffix + ".tmp")
        temp_path.write_text(rendered, encoding="utf-8")
        temp_path.replace(output_path)
        return output_path

    def _render_overview(self, report: MonthlyReport) -> str:
        quality_rows = "".join(
            "<tr>"
            f"<td>{row.business_stream}</td>"
            f"<td>{row.project_name}</td>"
            f"<td>{self._fmt(row.supported_releases_count)}</td>"
            f"<td>{self._fmt(row.bugs_found.p1_p2)}</td>"
            f"<td>{self._fmt(row.production_incidents.p1_p2)}</td>"
            f"<td>{self._fmt(row.defect_leakage.rate_percent)}</td>"
            "</tr>"
            for row in report.quality_metrics_rows
        )
        coverage_rows = "".join(
            "<tr>"
            f"<td>{row.business_stream}</td>"
            f"<td>{row.project_name}</td>"
            f"<td>{self._fmt(row.percentage_automation)}</td>"
            f"<td>{self._fmt(row.manual_total)}</td>"
            f"<td>{self._fmt(row.automated_total)}</td>"
            "</tr>"
            for row in report.test_coverage_rows
        )
        return (
            '<ac:structured-macro ac:name="info"><ac:rich-text-body>'
            f"<h1>Monthly QA Summary — {report.metadata.reporting_period}</h1>"
            f"<p>Completeness: {report.completeness.status}</p>"
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
            f"<td>{snapshot.month.to_iso_month()}</td>"
            f"<td>{self._fmt(snapshot.qa_metrics.get('manual_total'))}</td>"
            f"<td>{self._fmt(snapshot.qa_metrics.get('automated_total'))}</td>"
            f"<td>{self._fmt(snapshot.qa_metrics.get('percentage_automation'))}</td>"
            "</tr>"
            for snapshot in data.snapshots
        )
        return (
            f"<h1>Project Detail — {data.project_id.value}</h1>"
            "<table><tbody>"
            "<tr><th>Month</th><th>Manual</th><th>Automated</th><th>Automation %</th></tr>"
            f"{rows}"
            "</tbody></table>"
        )

    def _render_trends(self, data: TrendsDashboardData) -> str:
        months = ", ".join(month.to_iso_month() for month in data.months)
        sections = []
        for metric_name, series_list in data.qa_metric_series.items():
            series_rows = "".join(
                f"<tr><td>{series.label}</td><td>{', '.join(self._fmt(value) for value in series.values)}</td></tr>"
                for series in series_list
            )
            sections.append(f"<h2>{metric_name}</h2><table><tbody><tr><th>Project</th><th>Values</th></tr>{series_rows}</tbody></table>")
        return f"<h1>Trends</h1><p>Months: {months}</p>{''.join(sections)}"

    @staticmethod
    def _fmt(value: float | str | None) -> str:
        if value is None:
            return "-"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    @staticmethod
    def _smoke_check(rendered: str, file_name: str) -> None:
        """Ensure rendered Confluence content includes expected markers."""
        required = ["<h1>", "</table>"]
        missing = [marker for marker in required if marker not in rendered]
        if missing:
            message = f"Confluence dashboard render failed smoke check for {file_name}"
            raise DashboardRenderError(message)
