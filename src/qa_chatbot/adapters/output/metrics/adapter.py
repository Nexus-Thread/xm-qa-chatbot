"""In-memory metrics adapter."""

from __future__ import annotations

import logging
import math
import threading
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from qa_chatbot.application.ports import MetricsPort
from qa_chatbot.domain import InvalidMetricInputError

if TYPE_CHECKING:
    from _thread import LockType

    from qa_chatbot.domain import ProjectId, TimeWindow

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot of collected metrics."""

    submissions: int
    last_submission_at: datetime | None
    llm_latency_ms: dict[str, float]
    llm_latency_stats: dict[str, LatencyStatsSnapshot]


@dataclass(frozen=True)
class LatencyStatsSnapshot:
    """Aggregated latency statistics for one operation."""

    count: int
    total_ms: float
    min_ms: float
    max_ms: float
    avg_ms: float
    last_ms: float


@dataclass
class _LatencyAccumulator:
    """Mutable latency accumulator for in-memory tracking."""

    count: int = 0
    total_ms: float = 0.0
    min_ms: float = field(default_factory=lambda: math.inf)
    max_ms: float = field(default_factory=lambda: -math.inf)
    last_ms: float = 0.0

    def add_sample(self, elapsed_ms: float) -> None:
        """Add one latency sample."""
        self.count += 1
        self.total_ms += elapsed_ms
        self.min_ms = min(self.min_ms, elapsed_ms)
        self.max_ms = max(self.max_ms, elapsed_ms)
        self.last_ms = elapsed_ms

    def to_snapshot(self) -> LatencyStatsSnapshot:
        """Convert accumulator state to an immutable snapshot."""
        return LatencyStatsSnapshot(
            count=self.count,
            total_ms=self.total_ms,
            min_ms=self.min_ms,
            max_ms=self.max_ms,
            avg_ms=self.total_ms / self.count,
            last_ms=self.last_ms,
        )


@dataclass
class InMemoryMetricsAdapter(MetricsPort):
    """Store metrics in memory and log updates."""

    _lock: LockType = field(default_factory=threading.Lock, init=False, repr=False)
    submissions: int = 0
    last_submission_at: datetime | None = None
    llm_latency_ms: dict[str, float] = field(default_factory=dict)
    _llm_latency_stats: dict[str, _LatencyAccumulator] = field(default_factory=dict, init=False, repr=False)

    def record_submission(self, project_id: ProjectId, time_window: TimeWindow) -> None:
        """Record a successful submission event."""
        with self._lock:
            self.submissions += 1
            self.last_submission_at = datetime.now(tz=UTC)
            submission_count = self.submissions
        LOGGER.info(
            "Submission recorded",
            extra={
                "component": self.__class__.__name__,
                "project_id": str(project_id),
                "time_window": str(time_window),
                "submission_count": submission_count,
            },
        )

    def record_llm_latency(self, operation: str, elapsed_ms: float) -> None:
        """Record latency for an LLM extraction operation."""
        if not isinstance(operation, str):
            msg = "Operation name must be a string"
            raise InvalidMetricInputError(msg)
        normalized_operation = operation.strip()
        if not normalized_operation:
            msg = "Operation name must be a non-empty string"
            raise InvalidMetricInputError(msg)
        if elapsed_ms < 0 or not math.isfinite(elapsed_ms):
            msg = "Elapsed latency must be a finite, non-negative number"
            raise InvalidMetricInputError(msg)

        with self._lock:
            self.llm_latency_ms[normalized_operation] = elapsed_ms
            accumulator = self._llm_latency_stats.setdefault(normalized_operation, _LatencyAccumulator())
            accumulator.add_sample(elapsed_ms)
            sample_count = accumulator.count

        LOGGER.info(
            "LLM latency recorded",
            extra={
                "component": self.__class__.__name__,
                "operation": normalized_operation,
                "elapsed_ms": round(elapsed_ms, 2),
                "sample_count": sample_count,
            },
        )

    def snapshot(self) -> MetricsSnapshot:
        """Return a snapshot of stored metrics."""
        with self._lock:
            return MetricsSnapshot(
                submissions=self.submissions,
                last_submission_at=self.last_submission_at,
                llm_latency_ms=dict(self.llm_latency_ms),
                llm_latency_stats={operation: stats.to_snapshot() for operation, stats in self._llm_latency_stats.items()},
            )
