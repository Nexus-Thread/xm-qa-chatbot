"""Unit tests for health check adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.adapters.output.health.adapter import HealthCheckAdapter
from qa_chatbot.adapters.output.metrics import InMemoryMetricsAdapter

if TYPE_CHECKING:
    from qa_chatbot.domain import TeamId


@dataclass
class FakeStorage:
    """Storage port stub for health checks."""

    should_fail: bool = False

    def get_all_teams(self) -> list[TeamId]:
        """Return empty results or raise to simulate failure."""
        if self.should_fail:
            msg = "database offline"
            raise RuntimeError(msg)
        return []


def test_health_check_reports_ok_with_metrics() -> None:
    """Return ok status when database responds."""
    storage = FakeStorage()
    metrics = InMemoryMetricsAdapter()
    metrics.record_llm_latency("team_id", 12.5)
    adapter = HealthCheckAdapter(storage_port=storage, metrics_adapter=metrics)

    payload = adapter.build_payload()

    assert payload["status"] == "ok"
    assert payload["database_ok"] is True
    metrics_payload = payload["metrics"]
    assert metrics_payload["llm_latency_ms"] == {"team_id": 12.5}


def test_health_check_reports_degraded_on_failure() -> None:
    """Return degraded status when database errors."""
    storage = FakeStorage(should_fail=True)
    adapter = HealthCheckAdapter(storage_port=storage)

    payload = adapter.build_payload()

    assert payload["status"] == "degraded"
    assert payload["database_ok"] is False
