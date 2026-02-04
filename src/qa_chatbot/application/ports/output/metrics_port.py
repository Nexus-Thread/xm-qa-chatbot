"""Metrics port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, TimeWindow


class MetricsPort(Protocol):
    """Observability interface for application metrics."""

    def record_submission(self, team_id: ProjectId, time_window: TimeWindow) -> None:
        """Record a successful submission event."""

    def record_llm_latency(self, operation: str, elapsed_ms: float) -> None:
        """Record latency for an LLM extraction operation."""
