"""Submission entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from qa_chatbot.domain.exceptions import InvalidConfigurationError
from qa_chatbot.domain.services import ValidationService
from qa_chatbot.domain.value_objects import SubmissionMetrics

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import ProjectId, TestCoverageMetrics, TimeWindow


@dataclass(frozen=True)
class Submission:
    """Represents a single team submission for a time window."""

    id: UUID
    project_id: ProjectId
    month: TimeWindow
    test_coverage: TestCoverageMetrics | None
    overall_test_cases: int | None
    supported_releases_count: int | None
    created_at: datetime
    raw_conversation: str | None = None

    def __post_init__(self) -> None:
        """Ensure submissions contain at least one data category."""
        if self.created_at.tzinfo is None or self.created_at.utcoffset() is None:
            msg = "Submission created_at must be timezone-aware"
            raise InvalidConfigurationError(msg)
        ValidationService.ensure_submission_has_data(self.metrics)

    @property
    def metrics(self) -> SubmissionMetrics:
        """Return the validated submission metrics payload."""
        return SubmissionMetrics(
            test_coverage=self.test_coverage,
            overall_test_cases=self.overall_test_cases,
            supported_releases_count=self.supported_releases_count,
        )

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        project_id: ProjectId,
        month: TimeWindow,
        test_coverage: TestCoverageMetrics | None = None,
        overall_test_cases: int | None = None,
        supported_releases_count: int | None = None,
        raw_conversation: str | None = None,
        created_at: datetime | None = None,
        metrics: SubmissionMetrics | None = None,
    ) -> Submission:
        """Create a submission with generated identifiers."""
        if metrics is not None:
            if test_coverage is not None or overall_test_cases is not None or supported_releases_count is not None:
                msg = "Provide either metrics or scalar metric fields, not both"
                raise InvalidConfigurationError(msg)
            resolved_metrics = metrics
        else:
            resolved_metrics = SubmissionMetrics(
                test_coverage=test_coverage,
                overall_test_cases=overall_test_cases,
                supported_releases_count=supported_releases_count,
            )

        return cls(
            id=uuid4(),
            project_id=project_id,
            month=month,
            test_coverage=resolved_metrics.test_coverage,
            overall_test_cases=resolved_metrics.overall_test_cases,
            supported_releases_count=resolved_metrics.supported_releases_count,
            raw_conversation=raw_conversation,
            created_at=created_at or datetime.now(tz=UTC),
        )
