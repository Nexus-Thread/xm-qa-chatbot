"""Release support port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, ReportingPeriod


class ReleaseSupportPort(Protocol):
    """Port for supported releases data."""

    def fetch_supported_releases(self, project_id: ProjectId, period: ReportingPeriod) -> int:
        """Return supported releases count for the project and period."""
