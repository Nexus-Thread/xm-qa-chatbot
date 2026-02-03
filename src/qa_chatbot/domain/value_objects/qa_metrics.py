"""QA metrics value object."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidQAMetricsError


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
        """Validate QA metric values."""
        if self.tests_passed < 0 or self.tests_failed < 0:
            msg = "Test counts must be non-negative"
            raise InvalidQAMetricsError(msg)
        if self.test_coverage_percent is not None and not 0 <= self.test_coverage_percent <= 100:
            msg = "Test coverage must be between 0 and 100"
            raise InvalidQAMetricsError(msg)
        if self.bug_count is not None and self.bug_count < 0:
            msg = "Bug count must be non-negative"
            raise InvalidQAMetricsError(msg)
        if self.critical_bugs is not None and self.critical_bugs < 0:
            msg = "Critical bug count must be non-negative"
            raise InvalidQAMetricsError(msg)
