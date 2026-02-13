"""Quality and coverage metrics value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypeVar

from qa_chatbot.domain.exceptions import InvalidConfigurationError

T = TypeVar("T")


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
class CapaStatus:
    """CAPA status representation."""

    count: int | None
    status: str

    def __post_init__(self) -> None:
        """Validate CAPA status."""
        if self.status not in {"N/A", "OK", "MISSING_SOURCE"}:
            msg = "CAPA status must be N/A, OK, or MISSING_SOURCE"
            raise InvalidConfigurationError(msg)
        if self.count is not None and self.count < 0:
            msg = "CAPA count must be non-negative"
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


@dataclass(frozen=True)
class RegressionTimeEntry:
    """Single regression time entry."""

    category: str
    suite_name: str
    platform: str
    duration_minutes: float
    threads: int | None = None
    context_count: int | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        """Validate regression time entry values."""
        if self.duration_minutes < 0:
            msg = "Regression duration must be non-negative"
            raise InvalidConfigurationError(msg)
        if not self.suite_name.strip():
            msg = "Regression suite name is required"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class RegressionTimeBlock:
    """Collection of regression time entries."""

    entries: tuple[RegressionTimeEntry, ...] = field(default_factory=tuple)
    free_text_override: str | None = None


@dataclass(frozen=True)
class QualityMetrics:
    """Quality metrics for a project and period."""

    supported_releases_count: int
    bugs_found: BucketCount
    production_incidents: BucketCount
    capa: CapaStatus
    defect_leakage: DefectLeakage
    regression_time: RegressionTimeBlock

    def __post_init__(self) -> None:
        """Validate quality metrics fields."""
        if self.supported_releases_count < 0:
            msg = "Supported releases must be non-negative"
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
