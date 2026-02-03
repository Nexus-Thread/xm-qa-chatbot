"""Extract structured data from conversations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import ExtractionResult

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.ports.output import LLMPort


@dataclass(frozen=True)
class ExtractStructuredDataUseCase:
    """Orchestrate LLM extraction of structured data."""

    llm_port: LLMPort

    def execute(self, conversation: str, current_date: date) -> ExtractionResult:
        """Extract structured data from a conversation."""
        team_id = self.llm_port.extract_team_id(conversation)
        time_window = self.llm_port.extract_time_window(conversation, current_date)
        qa_metrics = self.llm_port.extract_qa_metrics(conversation)
        project_status = self.llm_port.extract_project_status(conversation)
        daily_update = self.llm_port.extract_daily_update(conversation)

        return ExtractionResult(
            team_id=team_id,
            time_window=time_window,
            qa_metrics=qa_metrics,
            project_status=project_status,
            daily_update=daily_update,
        )
