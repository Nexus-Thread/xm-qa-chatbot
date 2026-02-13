"""Unit tests for domain entities."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from qa_chatbot.domain import (
    InvalidTimeWindowError,
    ProjectId,
    ReportingPeriod,
    Submission,
    TestCoverageMetrics,
    TimeWindow,
)


def test_submission_allows_partial_data(project_id_a: ProjectId, time_window_jan: TimeWindow) -> None:
    """Allow partial submissions without coverage data."""
    submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=None,
        overall_test_cases=None,
    )

    assert submission.test_coverage is None


def test_submission_create_sets_defaults(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Populate missing submission defaults."""
    submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=test_coverage_done,
        overall_test_cases=None,
        created_at=datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC),
    )

    assert submission.id is not None
    assert submission.created_at == datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)


def test_reporting_period_for_month_builds_expected_bounds() -> None:
    """Build reporting period boundaries for a regular month."""
    period = ReportingPeriod.for_month(year=2026, month=2, timezone="Europe/Prague")

    assert period.iso_month == "2026-02"
    assert period.start_datetime == datetime(2026, 2, 1, 0, 0, tzinfo=period.start_datetime.tzinfo)
    assert period.end_datetime == datetime(2026, 3, 1, 0, 0, tzinfo=period.end_datetime.tzinfo)


def test_reporting_period_for_month_handles_december_rollover() -> None:
    """Build reporting period boundaries across year rollover."""
    period = ReportingPeriod.for_month(year=2026, month=12, timezone="Europe/Prague")

    assert period.iso_month == "2026-12"
    assert period.start_datetime == datetime(2026, 12, 1, 0, 0, tzinfo=period.start_datetime.tzinfo)
    assert period.end_datetime == datetime(2027, 1, 1, 0, 0, tzinfo=period.end_datetime.tzinfo)


def test_reporting_period_rejects_invalid_month() -> None:
    """Reject months outside calendar range."""
    with pytest.raises(InvalidTimeWindowError, match="Month must be between 1 and 12"):
        ReportingPeriod.for_month(year=2026, month=13, timezone="Europe/Prague")


def test_reporting_period_rejects_unknown_timezone() -> None:
    """Reject unsupported timezone names."""
    with pytest.raises(InvalidTimeWindowError, match="Unknown timezone"):
        ReportingPeriod.for_month(year=2026, month=2, timezone="Invalid/Timezone")


def test_reporting_period_from_time_window_rejects_non_integer_fields() -> None:
    """Reject non-integer coercion from TimeWindow-like values."""

    class InvalidWindow:
        year = "2026"
        month = "February"

    with pytest.raises(InvalidTimeWindowError, match="year and month must be integers"):
        ReportingPeriod.from_time_window(window=InvalidWindow(), timezone="Europe/Prague")


def test_reporting_period_rejects_inconsistent_direct_instantiation() -> None:
    """Reject direct construction with start datetime not matching year/month."""
    with pytest.raises(
        InvalidTimeWindowError,
        match="start must match the first day of year/month",
    ):
        ReportingPeriod(
            year=2026,
            month=2,
            start_datetime=datetime(2026, 2, 2, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2026, 3, 1, tzinfo=ZoneInfo("UTC")),
            timezone="UTC",
        )
