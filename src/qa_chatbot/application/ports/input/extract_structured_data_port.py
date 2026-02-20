"""Input port for extracting structured data."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
    from qa_chatbot.domain import ExtractionConfidence, ProjectId, TimeWindow
    from qa_chatbot.domain.registries import StreamProjectRegistry


class ExtractStructuredDataPort(Protocol):
    """Contract for structured data extraction use cases."""

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        """Extract project identifier with confidence."""

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract reporting time window from conversation."""

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        """Extract coverage metrics from conversation."""

    def execute(self, conversation: str, current_date: date, registry: StreamProjectRegistry) -> ExtractionResult:
        """Execute full extraction flow."""

    def execute_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        """Execute extraction flow with conversation history."""
