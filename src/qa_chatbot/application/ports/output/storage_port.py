"""Storage port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, Submission, TimeWindow


class StoragePort(Protocol):
    """Persistence interface for submissions."""

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission."""

    def get_submissions_by_project(
        self,
        project_id: ProjectId,
        month: TimeWindow,
    ) -> list[Submission]:
        """Retrieve submissions for a project and month."""

    def get_all_projects(self) -> list[ProjectId]:
        """Return all known projects."""

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a reporting month."""

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return the most recent reporting months."""
