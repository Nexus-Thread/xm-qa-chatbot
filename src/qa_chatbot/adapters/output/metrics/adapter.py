"""In-memory metrics adapter."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from qa_chatbot.application.ports import MetricsPort

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, TimeWindow


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot of collected metrics."""

    submissions: int
    last_submission_at: datetime | None
    llm_latency_ms: dict[str, float]


@dataclass
class InMemoryMetricsAdapter(MetricsPort):
    """Store metrics in memory and log updates."""

    _logger: logging.Logger = field(init=False, repr=False)
    submissions: int = 0
    last_submission_at: datetime | None = None
    llm_latency_ms: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Initialize logging for metrics."""
        self._logger = logging.getLogger(self.__class__.__name__)

    def record_submission(self, team_id: ProjectId, time_window: TimeWindow) -> None:
        """Record a successful submission event."""
        self.submissions += 1
        self.last_submission_at = datetime.now(tz=UTC)
        self._logger.info(
            "Submission recorded",
            extra={
                "project_id": str(team_id),
                "time_window": str(time_window),
                "submission_count": self.submissions,
            },
        )

    def record_llm_latency(self, operation: str, elapsed_ms: float) -> None:
        """Record latency for an LLM extraction operation."""
        self.llm_latency_ms[operation] = elapsed_ms
        self._logger.info(
            "LLM latency recorded",
            extra={
                "operation": operation,
                "elapsed_ms": round(elapsed_ms, 2),
            },
        )

    def snapshot(self) -> MetricsSnapshot:
        """Return a snapshot of stored metrics."""
        return MetricsSnapshot(
            submissions=self.submissions,
            last_submission_at=self.last_submission_at,
            llm_latency_ms=dict(self.llm_latency_ms),
        )
