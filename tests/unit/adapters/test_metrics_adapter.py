"""Unit tests for metrics adapter."""

from __future__ import annotations

from datetime import UTC, datetime

from qa_chatbot.adapters.output.metrics import InMemoryMetricsAdapter
from qa_chatbot.domain import ProjectId, TimeWindow


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

    adapter.record_llm_latency("project_id", 123.45)

    snapshot = adapter.snapshot()
    assert snapshot.llm_latency_ms == {"project_id": 123.45}
