"""Extract structured data from conversations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
from qa_chatbot.domain import SubmissionMetrics

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from qa_chatbot.application.ports.output import MetricsPort, StructuredExtractionPort
    from qa_chatbot.domain import ExtractionConfidence, ProjectId, TimeWindow
    from qa_chatbot.domain.registries import StreamProjectRegistry

ExtractedT = TypeVar("ExtractedT")


@dataclass(frozen=True)
class ExtractStructuredDataUseCase:
    """Orchestrate LLM extraction of structured data."""

    llm_port: StructuredExtractionPort
    metrics_port: MetricsPort | None = None

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        """Extract the project identifier from a conversation with confidence level."""
        return self._timed_extract("project_id", self.llm_port.extract_project_id, conversation, registry)

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        return self._timed_extract("time_window", self.llm_port.extract_time_window, conversation, current_date)

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        """Extract coverage metrics and supported releases from a conversation."""
        return self._timed_extract("coverage", self.llm_port.extract_coverage, conversation)

    def execute(self, conversation: str, current_date: date, registry: StreamProjectRegistry) -> ExtractionResult:
        """Extract structured data from a conversation."""
        project_id, _ = self.extract_project_id(conversation, registry)
        time_window = self.extract_time_window(conversation, current_date)
        coverage = self.extract_coverage(conversation)

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=coverage.metrics,
                overall_test_cases=None,
                supported_releases_count=coverage.supported_releases_count,
            ),
        )

    def execute_sections(
        self,
        conversation: str,
        current_date: date,
        registry: StreamProjectRegistry,
        *,
        include_test_coverage: bool,
    ) -> ExtractionResult:
        """Extract only the requested data sections from a conversation."""
        project_id, _ = self.extract_project_id(conversation, registry)
        time_window = self.extract_time_window(conversation, current_date)
        coverage = self.extract_coverage(conversation)
        test_coverage = coverage.metrics if include_test_coverage else None

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            metrics=SubmissionMetrics(
                test_coverage=test_coverage,
                overall_test_cases=None,
                supported_releases_count=coverage.supported_releases_count,
            ),
        )

    def execute_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
        if self.metrics_port is None:
            return self.llm_port.extract_with_history(request, current_date, registry)

        started_at = time.perf_counter()
        result = self.llm_port.extract_with_history(request, current_date, registry)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        self.metrics_port.record_llm_latency("history", elapsed_ms)
        return result

    def _timed_extract(
        self,
        operation: str,
        func: Callable[..., ExtractedT],
        *args: object,
    ) -> ExtractedT:
        """Time LLM operations and record latency metrics."""
        if self.metrics_port is None:
            return func(*args)
        started_at = time.perf_counter()
        result = func(*args)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        self.metrics_port.record_llm_latency(operation, elapsed_ms)
        return result
