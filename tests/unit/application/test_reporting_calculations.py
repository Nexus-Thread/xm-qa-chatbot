"""Unit tests for reporting calculation edge-case policies."""

from __future__ import annotations

from math import isnan

from qa_chatbot.application.services import EdgeCasePolicy, compute_portfolio_aggregates, format_regression_time
from qa_chatbot.domain import BucketCount, DefectLeakage, RegressionTimeBlock, RegressionTimeEntry

EXPECTED_AUTOMATION_PERCENTAGE = 33.33
EXPECTED_SUPPORTED_RELEASES_TOTAL = 6
EXPECTED_SUPPORTED_RELEASES_AVG = 3.0


def test_compute_automation_percentage_returns_nan_for_zero_total() -> None:
    """Return NaN when manual and automated totals are both zero."""
    policy = EdgeCasePolicy()

    result = policy.compute_automation_percentage(manual_total=0, automated_total=0)

    assert isnan(result)


def test_compute_defect_leakage_rate_returns_nan_for_zero_denominator() -> None:
    """Return NaN when denominator is zero."""
    policy = EdgeCasePolicy()

    result = policy.compute_defect_leakage_rate(numerator=0, denominator=0)

    assert isnan(result)


def test_compute_automation_percentage_uses_two_decimal_rounding() -> None:
    """Round automation percentage to two decimals."""
    policy = EdgeCasePolicy()

    result = policy.compute_automation_percentage(manual_total=2, automated_total=1)

    assert result == EXPECTED_AUTOMATION_PERCENTAGE


def test_format_regression_time_prefers_free_text_override() -> None:
    """Return free-text override entry when provided."""
    block = RegressionTimeBlock(
        entries=(
            RegressionTimeEntry(
                category="api",
                suite_name="Ignored",
                platform="web",
                duration_minutes=10,
            ),
        ),
        free_text_override="Manual regression only",
    )

    result = format_regression_time(block)

    assert result == (("Manual regression only", ""),)


def test_format_regression_time_formats_label_and_duration() -> None:
    """Format suite label extras and convert duration to minutes/hours."""
    block = RegressionTimeBlock(
        entries=(
            RegressionTimeEntry(
                category="api",
                suite_name="Smoke",
                platform="web",
                duration_minutes=45,
                context_count=3,
                threads=2,
                notes="critical",
            ),
            RegressionTimeEntry(
                category="api",
                suite_name="Full",
                platform="web",
                duration_minutes=120,
            ),
        ),
    )

    result = format_regression_time(block)

    assert result == (("Smoke (3) 2 threads critical", "45m"), ("Full", "2.0h"))


def test_compute_portfolio_aggregates_returns_expected_totals_and_averages() -> None:
    """Compute total and average values across streams."""
    result = compute_portfolio_aggregates(
        supported_releases=[4, 2],
        bugs=[BucketCount(p1_p2=1, p3_p4=3), BucketCount(p1_p2=3, p3_p4=1)],
        incidents=[BucketCount(p1_p2=0, p3_p4=2), BucketCount(p1_p2=2, p3_p4=0)],
        leakage=[
            DefectLeakage(numerator=1, denominator=4, rate_percent=25.0),
            DefectLeakage(numerator=3, denominator=6, rate_percent=50.0),
        ],
        rounding_decimals=2,
    )

    assert result.all_streams_supported_releases_total == EXPECTED_SUPPORTED_RELEASES_TOTAL
    assert result.all_streams_supported_releases_avg == EXPECTED_SUPPORTED_RELEASES_AVG
    assert result.all_streams_bugs_avg == BucketCount(p1_p2=2, p3_p4=2)
    assert result.all_streams_incidents_avg == BucketCount(p1_p2=1, p3_p4=1)
    assert result.all_streams_defect_leakage == DefectLeakage(numerator=4, denominator=10, rate_percent=40.0)


def test_compute_portfolio_aggregates_returns_zeroed_values_for_empty_inputs() -> None:
    """Return zeroed aggregate values for empty metric lists."""
    result = compute_portfolio_aggregates(
        supported_releases=[],
        bugs=[],
        incidents=[],
        leakage=[],
        rounding_decimals=2,
    )

    assert result.all_streams_supported_releases_total == 0
    assert result.all_streams_supported_releases_avg == 0.0
    assert result.all_streams_bugs_avg == BucketCount(p1_p2=0, p3_p4=0)
    assert result.all_streams_incidents_avg == BucketCount(p1_p2=0, p3_p4=0)
    assert result.all_streams_defect_leakage == DefectLeakage(numerator=0, denominator=0, rate_percent=0.0)
