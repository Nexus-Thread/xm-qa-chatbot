"""Submission metrics value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidConfigurationError, MissingSubmissionDataError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects.metrics import TestCoverageMetrics


@dataclass(frozen=True)
class SubmissionMetrics:
    """Validated metrics payload for a submission."""

    test_coverage: TestCoverageMetrics | None = None
    overall_test_cases: int | None = None
    supported_releases_count: int | None = None

    def __post_init__(self) -> None:
        """Validate submission metrics constraints."""
        self._validate_non_negative_optional(self.overall_test_cases, "Overall test cases")
        self._validate_non_negative_optional(self.supported_releases_count, "Supported releases count")
        if self.test_coverage is None and self.overall_test_cases is None and self.supported_releases_count is None:
            msg = "Submission must include test coverage, overall test cases, or supported releases count"
            raise MissingSubmissionDataError(msg)

    def merge_with(self, existing: SubmissionMetrics | None) -> SubmissionMetrics:
        """Merge with existing metrics while preserving provided values."""
        if existing is None:
            return self

        merged_coverage = self.test_coverage
        if merged_coverage is None:
            merged_coverage = existing.test_coverage
        elif existing.test_coverage is not None:
            merged_coverage = merged_coverage.merge_with(existing.test_coverage)

        merged_overall = self.overall_test_cases if self.overall_test_cases is not None else existing.overall_test_cases
        merged_supported_releases = (
            self.supported_releases_count if self.supported_releases_count is not None else existing.supported_releases_count
        )

        return SubmissionMetrics(
            test_coverage=merged_coverage,
            overall_test_cases=merged_overall,
            supported_releases_count=merged_supported_releases,
        )

    @staticmethod
    def _validate_non_negative_optional(value: int | None, field_name: str) -> None:
        """Validate optional integer fields are non-negative when provided."""
        if value is not None and value < 0:
            msg = f"{field_name} must be non-negative"
            raise InvalidConfigurationError(msg)
