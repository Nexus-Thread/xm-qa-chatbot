"""Submit structured team data for persistence."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qa_chatbot.domain import Submission

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import DashboardPort, MetricsPort, StoragePort


@dataclass(frozen=True)
class SubmitTeamDataUseCase:
    """Validate and persist a team submission."""

    storage_port: StoragePort
    dashboard_port: DashboardPort | None = None
    metrics_port: MetricsPort | None = None
    _logger: logging.Logger = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialize logging for the use case."""
        object.__setattr__(self, "_logger", logging.getLogger(self.__class__.__name__))

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a team submission and return it."""
        self._logger.info(
            "Submitting team data",
            extra={
                "team_id": str(command.team_id),
                "time_window": str(command.time_window),
            },
        )
        submission = Submission.create(
            team_id=command.team_id,
            month=command.time_window,
            qa_metrics=command.qa_metrics,
            project_status=command.project_status,
            daily_update=command.daily_update,
            raw_conversation=command.raw_conversation,
            created_at=command.created_at,
        )
        self.storage_port.save_submission(submission)
        if self.metrics_port is not None:
            self.metrics_port.record_submission(submission.team_id, submission.month)
        if self.dashboard_port is not None:
            recent_months = self.storage_port.get_recent_months(limit=6)
            teams = self.storage_port.get_all_teams()
            self.dashboard_port.generate_overview(submission.month)
            self.dashboard_port.generate_team_detail(submission.team_id, recent_months)
            self.dashboard_port.generate_trends(teams, recent_months)
        self._logger.info(
            "Submission saved",
            extra={
                "submission_id": submission.id,
                "team_id": str(submission.team_id),
                "time_window": str(submission.month),
            },
        )
        return submission
