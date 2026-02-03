"""LLM extraction port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.dtos import ExtractionResult
    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


class LLMPort(Protocol):
    """Protocol for extracting structured data from conversations."""

    def extract_team_id(self, conversation: str) -> TeamId:
        """Extract a team identifier from a conversation."""

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""

    def extract_qa_metrics(self, conversation: str) -> QAMetrics:
        """Extract QA metrics from a conversation."""

    def extract_project_status(self, conversation: str) -> ProjectStatus:
        """Extract project status updates from a conversation."""

    def extract_daily_update(self, conversation: str) -> DailyUpdate:
        """Extract a daily update from a conversation."""

    def extract_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
