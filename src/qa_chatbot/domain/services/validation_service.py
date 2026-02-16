"""Validation service for cross-entity checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import MissingSubmissionDataError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import TestCoverageMetrics


class ValidationService:
    """Performs cross-entity validation checks."""

    @staticmethod
    def ensure_submission_has_data(
        test_coverage: TestCoverageMetrics | None,
        overall_test_cases: int | None,
        supported_releases_count: int | None,
    ) -> None:
        """Validate submission data sections when required."""
        if test_coverage is None and overall_test_cases is None and supported_releases_count is None:
            msg = "Submission must include test coverage, overall test cases, or supported releases count"
            raise MissingSubmissionDataError(msg)
