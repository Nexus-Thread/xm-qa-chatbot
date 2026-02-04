"""Storage port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.domain import Submission, TeamId, TimeWindow


class StoragePort(Protocol):
    """Persistence interface for submissions."""

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission."""

    def get_submissions_by_team(
        self,
        team_id: TeamId,
        month: TimeWindow,
    ) -> list[Submission]:
        """Retrieve submissions for a team and month."""

    def get_all_teams(self) -> list[TeamId]:
        """Return all known teams."""

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a reporting month."""

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return the most recent reporting months."""
