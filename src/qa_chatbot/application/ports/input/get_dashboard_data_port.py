"""Input port for dashboard data queries."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import OverviewDashboardData, ProjectDetailDashboardData, TrendsDashboardData
    from qa_chatbot.domain import ProjectId, TimeWindow


class GetDashboardDataPort(Protocol):
    """Contract for dashboard data query use cases."""

    def build_overview(self, month: TimeWindow) -> OverviewDashboardData:
        """Build overview dashboard data for a month."""

    def build_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> ProjectDetailDashboardData:
        """Build project detail dashboard data."""

    def build_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> TrendsDashboardData:
        """Build trends dashboard data."""
