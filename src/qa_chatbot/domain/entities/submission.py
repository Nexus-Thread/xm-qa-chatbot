"""Submission entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from qa_chatbot.domain.services import ValidationService

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
        ValidationService.ensure_submission_has_data(
            test_coverage=self.test_coverage,
        )

    @classmethod
    def create(  # noqa: PLR0913
        cls,
        project_id: ProjectId,
        month: TimeWindow,
        test_coverage: TestCoverageMetrics | None,
        overall_test_cases: int | None,
        supported_releases_count: int | None = None,
        raw_conversation: str | None = None,
        created_at: datetime | None = None,
    ) -> Submission:
        """Create a submission with generated identifiers."""
        return cls(
            id=uuid4(),
            project_id=project_id,
            month=month,
            test_coverage=test_coverage,
            overall_test_cases=overall_test_cases,
            supported_releases_count=supported_releases_count,
            raw_conversation=raw_conversation,
            created_at=created_at or datetime.now(tz=UTC),
        )
