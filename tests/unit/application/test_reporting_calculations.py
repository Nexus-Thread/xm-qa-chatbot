"""Unit tests for reporting calculation edge-case policies."""

from __future__ import annotations

from math import isnan

from qa_chatbot.application.services import EdgeCasePolicy

EXPECTED_AUTOMATION_PERCENTAGE = 33.33


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
