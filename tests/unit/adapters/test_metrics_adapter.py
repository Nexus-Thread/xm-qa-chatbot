"""Unit tests for metrics adapter."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import cast

import pytest

from qa_chatbot.adapters.output.metrics import InMemoryMetricsAdapter
from qa_chatbot.domain import InvalidMetricInputError, ProjectId, TimeWindow

SINGLE_SAMPLE_MS = 123.45
FIRST_SAMPLE_MS = 10.0
SECOND_SAMPLE_MS = 20.0
THIRD_SAMPLE_MS = 30.0
HISTORY_SAMPLE_COUNT = 3
THREAD_COUNT = 5
SAMPLES_PER_THREAD = 100
EXPECTED_TOTAL_SAMPLES = THREAD_COUNT * SAMPLES_PER_THREAD
CONCURRENT_SAMPLE_MS = 1.0


def test_metrics_adapter_records_submission() -> None:
    """Track submission counts and timestamp."""
    adapter = InMemoryMetricsAdapter()

    adapter.record_submission(ProjectId("project-a"), TimeWindow.from_year_month(2026, 1))

    snapshot = adapter.snapshot()
    assert snapshot.submissions == 1
    assert isinstance(snapshot.last_submission_at, datetime)
    assert snapshot.last_submission_at.tzinfo == UTC


def test_metrics_adapter_records_latency() -> None:
    """Track latest LLM latency per operation."""
    adapter = InMemoryMetricsAdapter()

    adapter.record_llm_latency("project_id", SINGLE_SAMPLE_MS)

    snapshot = adapter.snapshot()
    assert snapshot.llm_latency_ms == {"project_id": SINGLE_SAMPLE_MS}
    assert snapshot.llm_latency_stats["project_id"].count == 1
    assert snapshot.llm_latency_stats["project_id"].total_ms == SINGLE_SAMPLE_MS
    assert snapshot.llm_latency_stats["project_id"].min_ms == SINGLE_SAMPLE_MS
    assert snapshot.llm_latency_stats["project_id"].max_ms == SINGLE_SAMPLE_MS
    assert snapshot.llm_latency_stats["project_id"].avg_ms == SINGLE_SAMPLE_MS
    assert snapshot.llm_latency_stats["project_id"].last_ms == SINGLE_SAMPLE_MS


def test_metrics_adapter_aggregates_multiple_latency_samples() -> None:
    """Aggregate latency samples per operation."""
    adapter = InMemoryMetricsAdapter()

    adapter.record_llm_latency("history", FIRST_SAMPLE_MS)
    adapter.record_llm_latency("history", SECOND_SAMPLE_MS)
    adapter.record_llm_latency("history", THIRD_SAMPLE_MS)

    snapshot = adapter.snapshot()
    assert snapshot.llm_latency_ms == {"history": THIRD_SAMPLE_MS}
    stats = snapshot.llm_latency_stats["history"]
    assert stats.count == HISTORY_SAMPLE_COUNT
    assert stats.total_ms == FIRST_SAMPLE_MS + SECOND_SAMPLE_MS + THIRD_SAMPLE_MS
    assert stats.min_ms == FIRST_SAMPLE_MS
    assert stats.max_ms == THIRD_SAMPLE_MS
    assert stats.avg_ms == SECOND_SAMPLE_MS
    assert stats.last_ms == THIRD_SAMPLE_MS


@pytest.mark.parametrize(
    ("operation", "elapsed_ms"),
    [
        ("", 5.0),
        ("   ", 5.0),
        (cast("str", None), 5.0),
        ("extract", -1.0),
        ("extract", float("inf")),
        ("extract", float("nan")),
    ],
)
def test_metrics_adapter_rejects_invalid_latency_input(operation: str, elapsed_ms: float) -> None:
    """Raise domain error when latency input is invalid."""
    adapter = InMemoryMetricsAdapter()

    with pytest.raises(InvalidMetricInputError):
        adapter.record_llm_latency(operation, elapsed_ms)


def test_metrics_adapter_handles_concurrent_updates() -> None:
    """Keep consistent state during concurrent metric writes."""
    adapter = InMemoryMetricsAdapter()
    project_id = ProjectId("project-a")
    time_window = TimeWindow.from_year_month(2026, 1)

    def _record_batch() -> None:
        for _ in range(SAMPLES_PER_THREAD):
            adapter.record_submission(project_id, time_window)
            adapter.record_llm_latency("extract", CONCURRENT_SAMPLE_MS)

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        futures = [executor.submit(_record_batch) for _ in range(THREAD_COUNT)]
        for future in futures:
            future.result()

    snapshot = adapter.snapshot()
    assert snapshot.submissions == EXPECTED_TOTAL_SAMPLES
    assert snapshot.llm_latency_ms["extract"] == CONCURRENT_SAMPLE_MS
    stats = snapshot.llm_latency_stats["extract"]
    assert stats.count == EXPECTED_TOTAL_SAMPLES
    assert stats.total_ms == EXPECTED_TOTAL_SAMPLES * CONCURRENT_SAMPLE_MS
    assert stats.min_ms == CONCURRENT_SAMPLE_MS
    assert stats.max_ms == CONCURRENT_SAMPLE_MS
    assert stats.avg_ms == CONCURRENT_SAMPLE_MS
    assert stats.last_ms == CONCURRENT_SAMPLE_MS
