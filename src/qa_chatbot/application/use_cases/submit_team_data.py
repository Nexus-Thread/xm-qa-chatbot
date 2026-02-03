"""Submit structured team data for persistence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain import Submission

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.application.ports.output import StoragePort


@dataclass(frozen=True)
class SubmitTeamDataUseCase:
    """Validate and persist a team submission."""

    storage_port: StoragePort

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
        return submission
