"""Extract structured data from conversations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import ExtractionResult

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.ports.output import LLMPort
    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


@dataclass(frozen=True)
class ExtractStructuredDataUseCase:
    """Orchestrate LLM extraction of structured data."""

    llm_port: LLMPort

    def extract_team_id(self, conversation: str) -> TeamId:
        """Extract the team identifier from a conversation."""
        return self.llm_port.extract_team_id(conversation)

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        return self.llm_port.extract_time_window(conversation, current_date)

    def extract_qa_metrics(self, conversation: str) -> QAMetrics:
        """Extract QA metrics from a conversation."""
        return self.llm_port.extract_qa_metrics(conversation)

    def extract_project_status(self, conversation: str) -> ProjectStatus:
        """Extract project status updates from a conversation."""
        return self.llm_port.extract_project_status(conversation)

    def extract_daily_update(self, conversation: str) -> DailyUpdate:
        """Extract daily update details from a conversation."""
        return self.llm_port.extract_daily_update(conversation)

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

    def execute_sections(
        self,
        conversation: str,
        current_date: date,
        *,
        include_qa_metrics: bool,
        include_project_status: bool,
        include_daily_update: bool,
    ) -> ExtractionResult:
        """Extract only the requested data sections from a conversation."""
        team_id = self.llm_port.extract_team_id(conversation)
        time_window = self.llm_port.extract_time_window(conversation, current_date)
        qa_metrics = self.llm_port.extract_qa_metrics(conversation) if include_qa_metrics else None
        project_status = self.llm_port.extract_project_status(conversation) if include_project_status else None
        daily_update = self.llm_port.extract_daily_update(conversation) if include_daily_update else None

        return ExtractionResult(
            team_id=team_id,
            time_window=time_window,
            qa_metrics=qa_metrics,
            project_status=project_status,
            daily_update=daily_update,
        )

    def execute_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
        return self.llm_port.extract_with_history(conversation, history, current_date)
