"""OpenAI adapter implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.application.ports.output import LLMPort

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


class OpenAIAdapter(LLMPort):
    """Extracts structured data using an OpenAI-compatible API."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        """Initialize the adapter configuration."""
        self._base_url = base_url
        self._api_key = api_key
        self._model = model

    def extract_team_id(self, conversation: str) -> TeamId:
        """Extract a team identifier from a conversation."""
        raise NotImplementedError

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        raise NotImplementedError

    def extract_qa_metrics(self, conversation: str) -> QAMetrics:
        """Extract QA metrics from a conversation."""
        raise NotImplementedError

    def extract_project_status(self, conversation: str) -> ProjectStatus:
        """Extract project status updates from a conversation."""
        raise NotImplementedError

    def extract_daily_update(self, conversation: str) -> DailyUpdate:
        """Extract a daily update from a conversation."""
        raise NotImplementedError
