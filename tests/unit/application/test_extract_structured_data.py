"""Unit tests for structured extraction orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.application.use_cases import ExtractStructuredDataUseCase
from qa_chatbot.domain import (
    ExtractionConfidence,
    ProjectId,
    SubmissionMetrics,
    TestCoverageMetrics,
    TimeWindow,
)
from qa_chatbot.domain.registries import StreamProjectRegistry

EXPECTED_SUPPORTED_RELEASES_COUNT = 3


@dataclass
class _FakeLLM:
    """Fake LLM adapter for extraction use-case tests."""

    extract_test_coverage_calls: int = 0
    execute_with_history_registry: StreamProjectRegistry | None = None

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        _ = conversation
        _ = registry
        return ProjectId("project-a"), ExtractionConfidence.high()

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        _ = conversation
        _ = current_date
        return TimeWindow.from_year_month(2026, 1)

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        _ = conversation
        self.extract_test_coverage_calls += 1
        return TestCoverageMetrics(
            manual_total=10,
            automated_total=5,
            manual_created_in_reporting_month=1,
            manual_updated_in_reporting_month=1,
            automated_created_in_reporting_month=1,
            automated_updated_in_reporting_month=1,
        )

    def extract_supported_releases_count(self, conversation: str) -> int | None:
        _ = conversation
        return EXPECTED_SUPPORTED_RELEASES_COUNT

    def extract_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        _ = conversation
        _ = history
        _ = current_date
        self.execute_with_history_registry = registry
        return ExtractionResult(
            project_id=ProjectId("project-a"),
            time_window=TimeWindow.from_year_month(2026, 1),
            metrics=SubmissionMetrics(
                test_coverage=TestCoverageMetrics(
                    manual_total=10,
                    automated_total=5,
                    manual_created_in_reporting_month=1,
                    manual_updated_in_reporting_month=1,
                    automated_created_in_reporting_month=1,
                    automated_updated_in_reporting_month=1,
                ),
                overall_test_cases=None,
                supported_releases_count=EXPECTED_SUPPORTED_RELEASES_COUNT,
            ),
        )


@dataclass
class _FakeMetrics:
    """Fake metrics adapter for extraction use-case tests."""

    latencies: list[tuple[str, float]] = field(default_factory=list)

    def record_submission(self, project_id: ProjectId, time_window: TimeWindow) -> None:
        _ = project_id
        _ = time_window

    def record_llm_latency(self, operation: str, elapsed_ms: float) -> None:
        self.latencies.append((operation, elapsed_ms))


def _registry() -> StreamProjectRegistry:
    return StreamProjectRegistry(streams=(), projects=())


def test_execute_sections_skips_test_coverage_when_not_requested() -> None:
    """Do not invoke test coverage extraction when include_test_coverage is false."""
    llm = _FakeLLM()
    use_case = ExtractStructuredDataUseCase(llm_port=llm)

    result = use_case.execute_sections(
        conversation="project and month only",
        current_date=date(2026, 2, 1),
        registry=_registry(),
        include_test_coverage=False,
    )

    assert llm.extract_test_coverage_calls == 0
    assert result.metrics.test_coverage is None
    assert result.metrics.supported_releases_count == EXPECTED_SUPPORTED_RELEASES_COUNT


def test_execute_with_history_passes_registry_to_llm_port() -> None:
    """Forward the configured registry for history-based extraction."""
    llm = _FakeLLM()
    use_case = ExtractStructuredDataUseCase(llm_port=llm)
    registry = _registry()

    use_case.execute_with_history(
        conversation="conversation",
        history=[{"role": "user", "content": "hello"}],
        current_date=date(2026, 2, 1),
        registry=registry,
    )

    assert llm.execute_with_history_registry is registry


def test_execute_with_history_records_latency_metric() -> None:
    """Record history latency metrics when metrics adapter is configured."""
    llm = _FakeLLM()
    metrics = _FakeMetrics()
    use_case = ExtractStructuredDataUseCase(llm_port=llm, metrics_port=metrics)

    use_case.execute_with_history(
        conversation="conversation",
        history=None,
        current_date=date(2026, 2, 1),
        registry=_registry(),
    )

    assert len(metrics.latencies) == 1
    assert metrics.latencies[0][0] == "history"
