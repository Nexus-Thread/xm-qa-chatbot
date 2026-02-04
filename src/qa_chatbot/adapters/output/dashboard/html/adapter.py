"""HTML dashboard generator adapter."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from jinja2 import Environment, FileSystemLoader, select_autoescape

from qa_chatbot.application.ports import DashboardPort, StoragePort
from qa_chatbot.application.use_cases import GetDashboardDataUseCase

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import (
        OverviewDashboardData,
        TeamDetailDashboardData,
        TrendsDashboardData,
    )
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
        file_name = f"team-{team_id.value.lower()}.html"
        return self._render_template(
            template_name="team_detail.html",
            output_name=file_name,
            context={"data": data},
        )

    def generate_trends(self, teams: list[TeamId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
        data = self._use_case.build_trends(teams, months)
        return self._render_template(
            template_name="trends.html",
            output_name="trends.html",
            context={"data": data},
        )

    def _render_template(
        self,
        *,
        template_name: str,
        output_name: str,
        context: dict[str, OverviewDashboardData | TeamDetailDashboardData | TrendsDashboardData],
    ) -> Path:
        template = self._environment.get_template(template_name)
        rendered = template.render(**context)
        output_path = self._output_dir / output_name
        return self._write_atomic(output_path, rendered)

    def _write_atomic(self, path: Path, content: str) -> Path:
        temp_path = path.with_suffix(path.suffix + ".tmp")
        temp_path.write_text(content, encoding="utf-8")
        temp_path.replace(path)
        return path
