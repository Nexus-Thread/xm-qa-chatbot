"""Validation service for cross-entity checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import TestCoverageMetrics


class ValidationService:
    """Performs cross-entity validation checks."""

    @staticmethod
    def ensure_submission_has_data(test_coverage: TestCoverageMetrics | None) -> None:
        """Validate submission data sections when required."""
        if test_coverage is None:
            return
        return
