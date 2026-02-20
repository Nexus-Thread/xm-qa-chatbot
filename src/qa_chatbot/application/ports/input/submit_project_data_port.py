"""Input port for submitting project data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.domain import Submission


class SubmitProjectDataPort(Protocol):
    """Contract for submission use cases."""

    def execute(self, command: SubmissionCommand) -> Submission:
        """Persist a project submission."""
