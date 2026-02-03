"""QA metrics value object."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import InvalidQAMetricsError


@dataclass(frozen=True)
class QAMetrics:
    """QA testing metrics for a reporting window."""

    tests_passed: int
    tests_failed: int
    test_coverage_percent: float | None = None
    bug_count: int | None = None
    critical_bugs: int | None = None
    deployment_ready: bool | None = None

    def __post_init__(self) -> None:
        if self.tests_passed < 0 or self.tests_failed < 0:
            raise InvalidQAMetricsError("Test counts must be non-negative")
        if self.test_coverage_percent is not None and not 0 <= self.test_coverage_percent <= 100:
            raise InvalidQAMetricsError("Test coverage must be between 0 and 100")
        if self.bug_count is not None and self.bug_count < 0:
            raise InvalidQAMetricsError("Bug count must be non-negative")
        if self.critical_bugs is not None and self.critical_bugs < 0:
            raise InvalidQAMetricsError("Critical bug count must be non-negative")