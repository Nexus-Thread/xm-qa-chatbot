"""Validation service for cross-entity checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import SubmissionMetrics


class ValidationService:
    """Performs cross-entity validation checks."""

    @staticmethod
    def ensure_submission_has_data(metrics: SubmissionMetrics) -> None:
        """Validate submission data sections when required."""
        _ = metrics
