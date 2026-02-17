"""Dashboard generation port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.domain import ProjectId, TimeWindow


class DashboardPort(Protocol):
    """Port for generating dashboard views."""

    def generate_overview(self, month: TimeWindow) -> Path:
        """Generate the overview dashboard for a month."""

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Generate the project detail dashboard for a month."""

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Generate the trends dashboard."""
