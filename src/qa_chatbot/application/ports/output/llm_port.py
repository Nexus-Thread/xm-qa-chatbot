"""LLM extraction port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.dtos import ExtractionResult
    from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow


class LLMPort(Protocol):
    """Protocol for extracting structured data from conversations."""

    def extract_project_id(self, conversation: str) -> ProjectId:
        """Extract a project identifier from a conversation."""

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        """Extract test coverage metrics from a conversation."""

    def extract_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
