"""HTML dashboard generator adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
from uuid import uuid4

from jinja2 import Environment, FileSystemLoader, select_autoescape

from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.application.ports import DashboardPort

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import ProjectDetailDashboardData, TrendsDashboardData, TrendSeries
    from qa_chatbot.application.use_cases import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
    from qa_chatbot.domain import ProjectId, TimeWindow

DEFAULT_TAILWIND_SCRIPT_SRC = "https://cdn.tailwindcss.com"
DEFAULT_PLOTLY_SCRIPT_SRC = "https://cdn.plot.ly/plotly-2.27.0.min.js"

SMOKE_CHECK_MARKERS_BY_TEMPLATE: dict[str, tuple[str, ...]] = {
    "overview.html": (
        "Monthly QA Summary",
        "Quality Metrics",
        "Test Coverage",
        "<table",
    ),
    "project_detail.html": (
        "Coverage Trend",
        "qaTrendChart",
        "Plotly.newPlot('qaTrendChart'",
    ),
    "trends.html": (
        "QA Trends",
        "manualChart",
        "automationChart",
        "Plotly.newPlot(",
    ),
}


@dataclass
class HtmlDashboardAdapter(DashboardPort):
    """Generate static HTML dashboards."""

    get_dashboard_data_use_case: GetDashboardDataUseCase
    generate_monthly_report_use_case: GenerateMonthlyReportUseCase
    output_dir: Path
    tailwind_script_src: str = DEFAULT_TAILWIND_SCRIPT_SRC
    plotly_script_src: str = DEFAULT_PLOTLY_SCRIPT_SRC

    def __post_init__(self) -> None:
        """Prepare template environment and output directory."""
        self._output_dir = self.output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)
        self._tailwind_script_src = self.tailwind_script_src
        self._plotly_script_src = self.plotly_script_src
        templates_dir = Path(__file__).parent / "templates"
        self._environment = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=select_autoescape(["html"]),
        )
        self._use_case = self.get_dashboard_data_use_case
        self._report_use_case = self.generate_monthly_report_use_case

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview dashboard for a month."""
        report = self._report_use_case.execute(month)
        return self._render_template(
            template_name="overview.html",
            output_name="overview.html",
            context={"report": report, "assets": self._assets_context()},
        )

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Generate the project detail dashboard."""
        data = self._use_case.build_project_detail(project_id, months)
        chart_payload = self._build_project_detail_chart_payload(data)
        file_name = f"project-{project_id.value.lower()}.html"
        return self._render_template(
            template_name="project_detail.html",
            output_name=file_name,
            context={
                "data": data,
                "chart_payload": chart_payload,
                "assets": self._assets_context(),
            },
        )

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
        data = self._use_case.build_trends(projects, months)
        chart_payload = self._build_chart_payload(data)
        return self._render_template(
            template_name="trends.html",
            output_name="trends.html",
            context={
                "data": data,
                "chart_payload": chart_payload,
                "assets": self._assets_context(),
            },
        )

    def _assets_context(self) -> dict[str, str]:
        """Build asset URLs for HTML templates."""
        return {
            "tailwind_script_src": self._tailwind_script_src,
            "plotly_script_src": self._plotly_script_src,
        }

    def _render_template(
        self,
        *,
        template_name: str,
        output_name: str,
        context: dict[str, object],
    ) -> Path:
        try:
            template = self._environment.get_template(template_name)
        except Exception as err:
            msg = f"Failed to load dashboard template: {template_name}"
            raise DashboardRenderError(msg) from err

        try:
            rendered = template.render(**context)
        except Exception as err:
            msg = f"Failed to render dashboard template: {template_name}"
            raise DashboardRenderError(msg) from err

        self._smoke_check(rendered, template_name)
        output_path = self._output_dir / output_name
        return self._write_atomic(output_path, rendered)

    def _write_atomic(self, path: Path, content: str) -> Path:
        temp_path = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(path)
        except Exception as err:
            if temp_path.exists():
                temp_path.unlink(missing_ok=True)
            msg = f"Failed to write dashboard output: {path}"
            raise DashboardRenderError(msg) from err
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
        """Ensure rendered HTML includes expected template markers."""
        markers = ["<!DOCTYPE html>", "</html>"]
        markers.extend(SMOKE_CHECK_MARKERS_BY_TEMPLATE.get(template_name, ()))
        missing = [marker for marker in markers if marker not in rendered]
        if missing:
            missing_text = ", ".join(repr(marker) for marker in missing)
            message = f"Dashboard template {template_name} failed smoke check. Missing markers: {missing_text}"
            raise DashboardRenderError(message)
