"""Submit structured team data for persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain import Submission

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import DashboardPort, StoragePort


@dataclass(frozen=True)
class SubmitTeamDataUseCase:
    """Validate and persist a team submission."""

    storage_port: StoragePort
    dashboard_port: DashboardPort | None = None

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a team submission and return it."""
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
        if self.dashboard_port is not None:
            recent_months = self.storage_port.get_recent_months(limit=6)
            teams = self.storage_port.get_all_teams()
            self.dashboard_port.generate_overview(submission.month)
            self.dashboard_port.generate_team_detail(submission.team_id, recent_months)
            self.dashboard_port.generate_trends(teams, recent_months)
        return submission
