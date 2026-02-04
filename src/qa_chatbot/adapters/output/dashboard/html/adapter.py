"""HTML dashboard generator adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from qa_chatbot.application.ports import DashboardPort, StoragePort
from qa_chatbot.application.use_cases import GetDashboardDataUseCase
from qa_chatbot.domain.exceptions import DashboardRenderError

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import TeamDetailDashboardData, TrendsDashboardData, TrendSeries
    from qa_chatbot.domain import TeamId, TimeWindow


@dataclass
class HtmlDashboardAdapter(DashboardPort):
    """Generate static HTML dashboards."""

    storage_port: StoragePort
    output_dir: Path

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

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview dashboard for a month."""
        data = self._use_case.build_overview(month)
        return self._render_template(
            template_name="overview.html",
            output_name="overview.html",
            context={"data": data},
        )

    def generate_team_detail(self, team_id: TeamId, months: list[TimeWindow]) -> Path:
        """Generate the team detail dashboard."""
        data = self._use_case.build_team_detail(team_id, months)
        chart_payload = self._build_team_detail_chart_payload(data)
        file_name = f"team-{team_id.value.lower()}.html"
        return self._render_template(
            template_name="team_detail.html",
            output_name=file_name,
            context={"data": data, "chart_payload": chart_payload},
        )

    def generate_trends(self, teams: list[TeamId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
        data = self._use_case.build_trends(teams, months)
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
        """Build JSON-serializable payloads for chart rendering."""
        return {
            "months": [month.to_iso_month() for month in data.months],
            "qa_metric_series": {
                metric: [self._series_payload(series) for series in series_list]
                for metric, series_list in data.qa_metric_series.items()
            },
            "project_metric_series": {
                metric: [self._series_payload(series) for series in series_list]
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
    def _build_team_detail_chart_payload(data: TeamDetailDashboardData) -> dict[str, object]:
        """Build JSON payloads for the team detail charts."""
        snapshots = data.snapshots
        return {
            "labels": [snapshot.month.to_iso_month() for snapshot in snapshots],
            "tests_passed": [snapshot.qa_metrics["tests_passed"] for snapshot in snapshots],
            "tests_failed": [snapshot.qa_metrics["tests_failed"] for snapshot in snapshots],
            "coverage": [snapshot.qa_metrics["test_coverage_percent"] for snapshot in snapshots],
        }

    @staticmethod
    def _smoke_check(rendered: str, template_name: str) -> None:
        """Ensure rendered HTML includes basic expected markers."""
        markers = ["<!DOCTYPE html>", "</html>"]
        missing = [marker for marker in markers if marker not in rendered]
        if missing:
            message = f"Dashboard template {template_name} failed smoke check"
            raise DashboardRenderError(message)
