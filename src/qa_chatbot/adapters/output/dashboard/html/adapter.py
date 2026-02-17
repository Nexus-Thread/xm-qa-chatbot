"""HTML dashboard generator adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.adapters.output.jira_mock import MockJiraAdapter
from qa_chatbot.application.ports import DashboardPort, StoragePort
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.application.use_cases import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
from qa_chatbot.domain import build_default_stream_project_registry

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import ProjectDetailDashboardData, TrendsDashboardData, TrendSeries
    from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass
class HtmlDashboardAdapter(DashboardPort):
    """Generate static HTML dashboards."""

    storage_port: StoragePort
    output_dir: Path
    jira_base_url: str
    jira_username: str
    jira_api_token: str
    report_timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Prepare template environment and output directory."""
        self._output_dir = self.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        templates_dir = Path(__file__).parent / "templates"
        self._environment = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html"]),
        )
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
        """Generate the overview dashboard for a month."""
        report = self._report_use_case.execute(month)
        return self._render_template(
            template_name="overview.html",
            output_name="overview.html",
            context={"report": report},
        )

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Generate the project detail dashboard."""
        data = self._use_case.build_project_detail(project_id, months)
        chart_payload = self._build_project_detail_chart_payload(data)
        file_name = f"project-{project_id.value.lower()}.html"
        return self._render_template(
            template_name="project_detail.html",
            output_name=file_name,
            context={"data": data, "chart_payload": chart_payload},
        )

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
        data = self._use_case.build_trends(projects, months)
        chart_payload = self._build_chart_payload(data)
        return self._render_template(
            template_name="trends.html",
            output_name="trends.html",
            context={"data": data, "chart_payload": chart_payload},
        )

    def _render_template(
        self,
        *,
        template_name: str,
        output_name: str,
        context: dict[str, object],
    ) -> Path:
        template = self._environment.get_template(template_name)
        rendered = template.render(**context)
        self._smoke_check(rendered, template_name)
        output_path = self._output_dir / output_name
        return self._write_atomic(output_path, rendered)

    def _write_atomic(self, path: Path, content: str) -> Path:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)
        return path

    def _build_chart_payload(self, data: TrendsDashboardData) -> dict[str, object]:
        """Build JSON-serializable payloads for chart rendering (chronological order)."""
        chronological_months = list(reversed(data.months))
        return {
            "months": [month.to_iso_month() for month in chronological_months],
            "qa_metric_series": {
                metric: [self._series_payload_reversed(series) for series in series_list]
                for metric, series_list in data.qa_metric_series.items()
            },
            "project_metric_series": {
                metric: [self._series_payload_reversed(series) for series in series_list]
                for metric, series_list in data.project_metric_series.items()
            },
        }

    @staticmethod
    def _series_payload(series: TrendSeries) -> dict[str, object]:
        """Convert a trend series into JSON-safe data."""
        label = series.label
        values = series.values
        return {"label": label, "values": list(values)}

    @staticmethod
    def _series_payload_reversed(series: TrendSeries) -> dict[str, object]:
        """Convert a trend series into JSON-safe data in chronological order."""
        return {"label": series.label, "values": list(reversed(series.values))}

    @staticmethod
    def _build_project_detail_chart_payload(data: ProjectDetailDashboardData) -> dict[str, object]:
        """Build JSON payloads for the project detail charts (chronological order)."""
        chronological = list(reversed(data.snapshots))
        return {
            "labels": [snapshot.month.to_iso_month() for snapshot in chronological],
            "manual_total": [snapshot.qa_metrics["manual_total"] for snapshot in chronological],
            "automated_total": [snapshot.qa_metrics["automated_total"] for snapshot in chronological],
            "percentage_automation": [snapshot.qa_metrics["percentage_automation"] for snapshot in chronological],
        }

    @staticmethod
    def _smoke_check(rendered: str, template_name: str) -> None:
        """Ensure rendered HTML includes basic expected markers."""
        markers = ["<!DOCTYPE html>", "</html>"]
        missing = [marker for marker in markers if marker not in rendered]
        if missing:
            message = f"Dashboard template {template_name} failed smoke check"
            raise DashboardRenderError(message)
