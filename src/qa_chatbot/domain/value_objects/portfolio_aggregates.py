"""Portfolio aggregates value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects.metrics import BucketCount, DefectLeakage


@dataclass(frozen=True)
class PortfolioAggregates:
    """Aggregate metrics across all streams."""

    all_streams_supported_releases_total: int
    all_streams_supported_releases_avg: float
    all_streams_bugs_avg: BucketCount
    all_streams_incidents_avg: BucketCount
    all_streams_defect_leakage: DefectLeakage
