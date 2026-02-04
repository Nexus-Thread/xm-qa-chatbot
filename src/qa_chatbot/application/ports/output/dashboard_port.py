"""Dashboard generation port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.domain import TeamId, TimeWindow


class DashboardPort(Protocol):
    """Port for generating dashboard views."""

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview dashboard for a month."""

    def generate_team_detail(self, team_id: TeamId, months: list[TimeWindow]) -> Path:
        """Generate the team detail dashboard."""

    def generate_trends(self, teams: list[TeamId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
