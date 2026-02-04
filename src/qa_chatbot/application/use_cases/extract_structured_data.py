"""Extract structured data from conversations."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, TypeVar

from qa_chatbot.application.dtos import ExtractionResult

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from qa_chatbot.application.ports.output import LLMPort, MetricsPort
    from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow

ExtractedT = TypeVar("ExtractedT")


@dataclass(frozen=True)
class ExtractStructuredDataUseCase:
    """Orchestrate LLM extraction of structured data."""

    llm_port: LLMPort
    metrics_port: MetricsPort | None = None

    def extract_project_id(self, conversation: str) -> ProjectId:
        """Extract the project identifier from a conversation."""
        return self._timed_extract("project_id", self.llm_port.extract_project_id, conversation)

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Extract the reporting time window."""
        return self._timed_extract("time_window", self.llm_port.extract_time_window, conversation, current_date)

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        """Extract test coverage metrics from a conversation."""
        return self._timed_extract("test_coverage", self.llm_port.extract_test_coverage, conversation)

    def extract_overall_test_cases(self, conversation: str) -> int | None:
        """Extract overall portfolio test cases from a conversation."""
        return self._timed_extract("overall_test_cases", self.llm_port.extract_overall_test_cases, conversation)

    def execute(self, conversation: str, current_date: date) -> ExtractionResult:
        """Extract structured data from a conversation."""
        project_id = self.extract_project_id(conversation)
        time_window = self.extract_time_window(conversation, current_date)
        test_coverage = self.extract_test_coverage(conversation)
        overall_test_cases = self.extract_overall_test_cases(conversation)

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            test_coverage=test_coverage,
            overall_test_cases=overall_test_cases,
        )

    def execute_sections(
        self,
        conversation: str,
        current_date: date,
        *,
        include_test_coverage: bool,
        include_overall_test_cases: bool,
    ) -> ExtractionResult:
        """Extract only the requested data sections from a conversation."""
        project_id = self.extract_project_id(conversation)
        time_window = self.extract_time_window(conversation, current_date)
        test_coverage = self.extract_test_coverage(conversation) if include_test_coverage else None
        overall_test_cases = self.extract_overall_test_cases(conversation) if include_overall_test_cases else None

        return ExtractionResult(
            project_id=project_id,
            time_window=time_window,
            test_coverage=test_coverage,
            overall_test_cases=overall_test_cases,
        )

    def execute_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
    ) -> ExtractionResult:
        """Extract structured data using conversation history."""
        if self.metrics_port is None:
            return self.llm_port.extract_with_history(conversation, history, current_date)

        started_at = time.perf_counter()
        result = self.llm_port.extract_with_history(conversation, history, current_date)
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
