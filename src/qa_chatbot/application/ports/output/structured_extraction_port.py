"""Structured extraction port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
    from qa_chatbot.domain import ExtractionConfidence, ProjectId, TimeWindow
    from qa_chatbot.domain.registries import StreamProjectRegistry


class StructuredExtractionPort(Protocol):
    """Protocol for extracting structured data from conversations."""

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        """Extract a project identifier from a conversation with confidence level."""

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        """Extract coverage metrics and supported releases from a conversation."""

    def extract_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        """Extract selected structured data using conversation history and known values."""
