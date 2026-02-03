"""Team data aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidSubmissionTeamError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import TeamId, TimeWindow

    from .submission import Submission


@dataclass
class TeamData:
    """Aggregate of submissions for a team."""

    team_id: TeamId
    submissions: list[Submission] = field(default_factory=list)

    def add_submission(self, submission: Submission) -> None:
        """Add a submission for the team."""
        if submission.team_id != self.team_id:
            msg = "Submission team_id does not match TeamData"
            raise InvalidSubmissionTeamError(msg)
        self.submissions.append(submission)

    def submissions_for_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a given month."""
        return [submission for submission in self.submissions if submission.month == month]
