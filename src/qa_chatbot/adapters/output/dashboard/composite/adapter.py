"""Composite dashboard adapter that fans out generation to multiple adapters."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.ports import DashboardPort
from qa_chatbot.domain.exceptions import DashboardRenderError

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass
class CompositeDashboardAdapter(DashboardPort):
    """Dispatch dashboard generation to multiple output adapters."""

    adapters: tuple[DashboardPort, ...]

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview dashboard across all configured adapters."""
        return self._generate(lambda adapter: adapter.generate_overview(month))

    def generate_team_detail(self, team_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Generate the team detail dashboard across all configured adapters."""
        return self._generate(lambda adapter: adapter.generate_team_detail(team_id, months))

    def generate_trends(self, teams: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard across all configured adapters."""
        return self._generate(lambda adapter: adapter.generate_trends(teams, months))

    def _generate(self, generator: Callable[[DashboardPort], Path]) -> Path:
        if not self.adapters:
            msg = "At least one dashboard adapter must be configured"
            raise DashboardRenderError(msg)
        paths = [generator(adapter) for adapter in self.adapters]
        return paths[0]
