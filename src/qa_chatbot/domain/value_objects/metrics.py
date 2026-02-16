"""Quality and coverage metrics value objects."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TypeVar

from qa_chatbot.domain.exceptions import InvalidConfigurationError

T = TypeVar("T")
PERCENTAGE_MIN = 0.0
PERCENTAGE_MAX = 100.0


@dataclass(frozen=True)
class BucketCount:
    """Bucketed count values."""

    p1_p2: int
    p3_p4: int

    def __post_init__(self) -> None:
        """Validate bucketed counts."""
        if self.p1_p2 < 0 or self.p3_p4 < 0:
            msg = "Bucketed counts must be non-negative"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class DefectLeakage:
    """Defect leakage metrics."""

    numerator: int
    denominator: int
    rate_percent: float

    def __post_init__(self) -> None:
        """Validate leakage values."""
        if self.numerator < 0 or self.denominator < 0:
            msg = "Defect leakage counts must be non-negative"
            raise InvalidConfigurationError(msg)
        if not math.isfinite(self.rate_percent):
            msg = "Defect leakage rate must be a finite number"
            raise InvalidConfigurationError(msg)
        if self.rate_percent < PERCENTAGE_MIN or self.rate_percent > PERCENTAGE_MAX:
            msg = "Defect leakage rate must be between 0 and 100"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class QualityMetrics:
    """Quality metrics for a project and period."""

    supported_releases_count: int
    bugs_found: BucketCount
    production_incidents: BucketCount
    defect_leakage: DefectLeakage

    def __post_init__(self) -> None:
        """Validate quality metrics fields."""
        if self.supported_releases_count < 0:
            msg = "Supported releases must be non-negative"
            raise InvalidConfigurationError(msg)
        self._ensure_type(self.bugs_found, BucketCount, "bugs_found")
        self._ensure_type(self.production_incidents, BucketCount, "production_incidents")
        self._ensure_type(self.defect_leakage, DefectLeakage, "defect_leakage")

    @staticmethod
    def _ensure_type(value: object, expected_type: type[object], label: str) -> None:
        """Validate runtime type for nested metric value objects."""
        if not isinstance(value, expected_type):
            msg = f"{label} must be {expected_type.__name__}"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class TestCoverageMetrics:
    """Test coverage metrics for a project and period."""

    __test__ = False

    manual_total: int | None = None
    automated_total: int | None = None
    manual_created_in_reporting_month: int | None = None
    manual_updated_in_reporting_month: int | None = None
    automated_created_in_reporting_month: int | None = None
    automated_updated_in_reporting_month: int | None = None
    percentage_automation: float | None = None

    @staticmethod
    def _pick(current: T | None, existing: T | None) -> T | None:
        """Return current value when provided, otherwise fallback to existing."""
        return current if current is not None else existing

    def __post_init__(self) -> None:
        """Validate coverage metrics values."""
        counts = [
            self.manual_total,
            self.automated_total,
            self.manual_created_in_reporting_month,
            self.manual_updated_in_reporting_month,
            self.automated_created_in_reporting_month,
            self.automated_updated_in_reporting_month,
        ]
        if any(count is not None and count < 0 for count in counts):
            msg = "Test coverage counts must be non-negative"
            raise InvalidConfigurationError(msg)
        if self.percentage_automation is not None:
            if not math.isfinite(self.percentage_automation):
                msg = "Automation percentage must be a finite number"
                raise InvalidConfigurationError(msg)
            if self.percentage_automation < PERCENTAGE_MIN or self.percentage_automation > PERCENTAGE_MAX:
                msg = "Automation percentage must be between 0 and 100"
                raise InvalidConfigurationError(msg)

    def merge_with(self, existing: TestCoverageMetrics | None) -> TestCoverageMetrics:
        """Fill None fields from an existing record, keeping provided values."""
        if existing is None:
            return self
        return TestCoverageMetrics(
            manual_total=self._pick(self.manual_total, existing.manual_total),
            automated_total=self._pick(self.automated_total, existing.automated_total),
            manual_created_in_reporting_month=self._pick(
                self.manual_created_in_reporting_month,
                existing.manual_created_in_reporting_month,
            ),
            manual_updated_in_reporting_month=self._pick(
                self.manual_updated_in_reporting_month,
                existing.manual_updated_in_reporting_month,
            ),
            automated_created_in_reporting_month=self._pick(
                self.automated_created_in_reporting_month,
                existing.automated_created_in_reporting_month,
            ),
            automated_updated_in_reporting_month=self._pick(
                self.automated_updated_in_reporting_month,
                existing.automated_updated_in_reporting_month,
            ),
            percentage_automation=self._pick(
                self.percentage_automation,
                existing.percentage_automation,
            ),
        )
