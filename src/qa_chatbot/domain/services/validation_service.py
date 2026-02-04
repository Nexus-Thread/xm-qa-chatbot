"""Validation service for cross-entity checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import MissingSubmissionDataError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import DailyUpdate, ProjectStatus, QAMetrics


class ValidationService:
    """Performs cross-entity validation checks."""

    @staticmethod
    def ensure_submission_has_data(
        qa_metrics: QAMetrics | None,
        project_status: ProjectStatus | None,
        daily_update: DailyUpdate | None,
    ) -> None:
        """Ensure at least one data section is present."""
        if not (qa_metrics or project_status or daily_update):
            msg = "Submission must include at least one data section"
            raise MissingSubmissionDataError(msg)
