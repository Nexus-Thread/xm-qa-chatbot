"""Unit tests for submission metrics merge behavior."""

from qa_chatbot.domain import SubmissionMetrics, TestCoverageMetrics

UPDATED_OVERALL_TEST_CASES = 40
UPDATED_SUPPORTED_RELEASES_COUNT = 4


def _coverage(*, manual_total: int, automated_total: int) -> TestCoverageMetrics:
    """Create a minimal coverage payload for submission metrics tests."""
    return TestCoverageMetrics(manual_total=manual_total, automated_total=automated_total)


def test_merge_with_none_existing_returns_current_metrics() -> None:
    """Return the current metrics unchanged when existing metrics are absent."""
    current = SubmissionMetrics(
        test_coverage=_coverage(manual_total=10, automated_total=5),
        overall_test_cases=15,
        supported_releases_count=2,
    )

    merged = current.merge_with(None)

    assert merged == current


def test_merge_with_existing_uses_existing_coverage_when_current_missing() -> None:
    """Fallback to existing coverage when the current update does not include it."""
    existing_coverage = _coverage(manual_total=20, automated_total=10)
    existing = SubmissionMetrics(
        test_coverage=existing_coverage,
        overall_test_cases=30,
        supported_releases_count=3,
    )
    current = SubmissionMetrics(
        test_coverage=None,
        overall_test_cases=40,
        supported_releases_count=4,
    )

    merged = current.merge_with(existing)

    assert merged.test_coverage == existing_coverage
    assert merged.overall_test_cases == UPDATED_OVERALL_TEST_CASES
    assert merged.supported_releases_count == UPDATED_SUPPORTED_RELEASES_COUNT
