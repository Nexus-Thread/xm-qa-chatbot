"""Validation service for cross-entity checks."""

from __future__ import annotations

from ..exceptions import MissingSubmissionDataError
from ..value_objects import DailyUpdate, ProjectStatus, QAMetrics


class ValidationService:
    """Performs cross-entity validation checks."""

    @staticmethod
    def ensure_submission_has_data(
        qa_metrics: QAMetrics | None,
        project_status: ProjectStatus | None,
        daily_update: DailyUpdate | None,
    ) -> None:
        """Ensure at least one data section is present."""

        if not any([qa_metrics, project_status, daily_update]):
            raise MissingSubmissionDataError("Submission must include at least one data section")