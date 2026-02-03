"""Unit tests for domain value objects."""

from datetime import date

import pytest

from qa_chatbot.domain import (
    DailyUpdate,
    InvalidDailyUpdateError,
    InvalidProjectStatusError,
    InvalidQAMetricsError,
    InvalidTeamIdError,
    InvalidTimeWindowError,
    ProjectStatus,
    QAMetrics,
    TeamId,
    TimeWindow,
)


def test_team_id_normalizes_value() -> None:
    """Normalize team identifiers."""
    team_id = TeamId.from_raw("  Alpha ")

    assert team_id.value == "Alpha"


def test_team_id_rejects_empty_value() -> None:
    """Reject empty team identifiers."""
    with pytest.raises(InvalidTeamIdError):
        TeamId.from_raw("  ")


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


def test_qa_metrics_validates_counts() -> None:
    """Reject invalid QA metric values."""
    with pytest.raises(InvalidQAMetricsError):
        QAMetrics(tests_passed=-1, tests_failed=0)

    with pytest.raises(InvalidQAMetricsError):
        QAMetrics(tests_passed=1, tests_failed=0, test_coverage_percent=120)


def test_project_status_validates_content() -> None:
    """Reject invalid project status values."""
    with pytest.raises(InvalidProjectStatusError):
        ProjectStatus(blockers=(" ",))


def test_daily_update_validates_capacity_and_items() -> None:
    """Reject invalid daily update values."""
    with pytest.raises(InvalidDailyUpdateError):
        DailyUpdate(capacity_hours=-1)

    with pytest.raises(InvalidDailyUpdateError):
        DailyUpdate(completed_tasks=("",))
