"""Portfolio aggregates value object."""

from __future__ import annotations

import math
from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidConfigurationError
from qa_chatbot.domain.value_objects.metrics import BucketCount, DefectLeakage


@dataclass(frozen=True)
class PortfolioAggregates:
    """Aggregate metrics across all streams."""

    all_streams_supported_releases_total: int
    all_streams_supported_releases_avg: float
    all_streams_bugs_avg: BucketCount
    all_streams_incidents_avg: BucketCount
    all_streams_defect_leakage: DefectLeakage

    def __post_init__(self) -> None:
        """Validate aggregate metrics fields."""
        if self.all_streams_supported_releases_total < 0:
            msg = "Supported releases total must be non-negative"
            raise InvalidConfigurationError(msg)
        if not math.isfinite(self.all_streams_supported_releases_avg):
            msg = "Supported releases average must be a finite number"
            raise InvalidConfigurationError(msg)
        if self.all_streams_supported_releases_avg < 0:
            msg = "Supported releases average must be non-negative"
            raise InvalidConfigurationError(msg)
        self._ensure_type(
            value=self.all_streams_bugs_avg,
            expected_type=BucketCount,
            label="all_streams_bugs_avg",
        )
        self._ensure_type(
            value=self.all_streams_incidents_avg,
            expected_type=BucketCount,
            label="all_streams_incidents_avg",
        )
        self._ensure_type(
            value=self.all_streams_defect_leakage,
            expected_type=DefectLeakage,
            label="all_streams_defect_leakage",
        )

    @staticmethod
    def _ensure_type(value: object, expected_type: type[object], label: str) -> None:
        """Validate runtime type for aggregate nested value objects."""
        if not isinstance(value, expected_type):
            msg = f"{label} must be {expected_type.__name__}"
            raise InvalidConfigurationError(msg)
