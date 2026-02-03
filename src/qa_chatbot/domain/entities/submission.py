"""Submission entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from ..services import ValidationService
from ..value_objects import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


@dataclass(frozen=True)
class Submission:
    """Represents a single team submission for a time window."""

    id: UUID
    team_id: TeamId
    month: TimeWindow
    qa_metrics: QAMetrics | None
    project_status: ProjectStatus | None
    daily_update: DailyUpdate | None
    created_at: datetime
    raw_conversation: str | None = None

    def __post_init__(self) -> None:
        ValidationService.ensure_submission_has_data(
            qa_metrics=self.qa_metrics,
            project_status=self.project_status,
            daily_update=self.daily_update,
        )

    @classmethod
    def create(
        cls,
        team_id: TeamId,
        month: TimeWindow,
        qa_metrics: QAMetrics | None,
        project_status: ProjectStatus | None,
        daily_update: DailyUpdate | None,
        raw_conversation: str | None = None,
        created_at: datetime | None = None,
    ) -> "Submission":
        """Create a submission with generated identifiers."""

        return cls(
            id=uuid4(),
            team_id=team_id,
            month=month,
            qa_metrics=qa_metrics,
            project_status=project_status,
            daily_update=daily_update,
            raw_conversation=raw_conversation,
            created_at=created_at or datetime.utcnow(),
        )