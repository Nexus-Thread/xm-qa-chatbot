"""Unit tests for domain value objects."""

from datetime import date

import pytest

from qa_chatbot.domain import (
    InvalidProjectIdError,
    InvalidTimeWindowError,
    ProjectId,
    TestCoverageMetrics,
    TimeWindow,
)


def test_project_id_normalizes_value() -> None:
    """Normalize project identifiers."""
    project_id = ProjectId.from_raw("  Alpha ")

    assert project_id.value == "Alpha"


def test_project_id_rejects_empty_value() -> None:
    """Reject empty project identifiers."""
    with pytest.raises(InvalidProjectIdError):
        ProjectId.from_raw("  ")


def test_time_window_validates_ranges() -> None:
    """Validate time window ranges."""
    with pytest.raises(InvalidTimeWindowError):
        TimeWindow.from_year_month(year=1999, month=1)

    with pytest.raises(InvalidTimeWindowError):
        TimeWindow.from_year_month(year=2024, month=13)


def test_time_window_default_uses_previous_month_within_grace() -> None:
    """Use previous month within grace period."""
    window = TimeWindow.default_for(date(2026, 2, 1), grace_period_days=2)

    assert window.to_iso_month() == "2026-01"


def test_time_window_default_uses_current_month_after_grace() -> None:
    """Use current month after grace period."""
    window = TimeWindow.default_for(date(2026, 2, 3), grace_period_days=2)

    assert window.to_iso_month() == "2026-02"


def test_test_coverage_rejects_negative_counts() -> None:
    """Reject invalid coverage metrics values."""
    with pytest.raises(ValueError, match="Test coverage counts must be non-negative"):
        TestCoverageMetrics(
            manual_total=-1,
            automated_total=0,
            manual_created_last_month=0,
            manual_updated_last_month=0,
            automated_created_last_month=0,
            automated_updated_last_month=0,
            percentage_automation=0.0,
        )
