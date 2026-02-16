"""Unit tests for domain entities."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pytest

from qa_chatbot.domain import (
    BusinessStream,
    InvalidConfigurationError,
    InvalidTimeWindowError,
    MissingSubmissionDataError,
    Project,
    ProjectId,
    ReportingPeriod,
    StreamId,
    Submission,
    TestCoverageMetrics,
    TimeWindow,
)

SUPPORTED_RELEASES_ONLY_COUNT = 3


def test_business_stream_rejects_blank_name() -> None:
    """Reject business stream with blank display name."""
    with pytest.raises(InvalidConfigurationError, match="Business stream name must be provided"):
        BusinessStream(id=StreamId("stream-a"), name="   ", order=1)


def test_business_stream_rejects_negative_order() -> None:
    """Reject business stream with negative order."""
    with pytest.raises(InvalidConfigurationError, match="Business stream order must be non-negative"):
        BusinessStream(id=StreamId("stream-a"), name="Stream A", order=-1)


def test_project_rejects_blank_identity_fields() -> None:
    """Reject project with blank id or name."""
    with pytest.raises(InvalidConfigurationError, match="Project id and name are required"):
        Project(id="  ", name="Valid Name", business_stream_id=StreamId("stream-a"))

    with pytest.raises(InvalidConfigurationError, match="Project id and name are required"):
        Project(id="project-a", name="  ", business_stream_id=StreamId("stream-a"))


def test_submission_rejects_when_all_metrics_missing(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Reject submissions that contain no metric category."""
    with pytest.raises(
        MissingSubmissionDataError,
        match="Submission must include test coverage, overall test cases, or supported releases count",
    ):
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=None,
            overall_test_cases=None,
            supported_releases_count=None,
        )


def test_submission_allows_partial_data_with_supported_releases_only(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Allow partial submissions with at least one metric category."""
    submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=None,
        overall_test_cases=None,
        supported_releases_count=SUPPORTED_RELEASES_ONLY_COUNT,
    )

    assert submission.test_coverage is None
    assert submission.supported_releases_count == SUPPORTED_RELEASES_ONLY_COUNT


def test_submission_rejects_negative_overall_test_cases(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Reject negative overall test cases."""
    with pytest.raises(InvalidConfigurationError, match="Overall test cases must be non-negative"):
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=test_coverage_done,
            overall_test_cases=-1,
        )


def test_submission_rejects_negative_supported_releases_count(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Reject negative supported releases count."""
    with pytest.raises(InvalidConfigurationError, match="Supported releases count must be non-negative"):
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=test_coverage_done,
            overall_test_cases=None,
            supported_releases_count=-1,
        )


def test_submission_rejects_naive_created_at(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Reject submissions created with naive datetime values."""
    naive_created_at = datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC).replace(tzinfo=None)
    with pytest.raises(InvalidConfigurationError, match="Submission created_at must be timezone-aware"):
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=test_coverage_done,
            overall_test_cases=None,
            created_at=naive_created_at,
        )


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


def test_reporting_period_rejects_non_integer_month() -> None:
    """Reject non-integer month values."""
    with pytest.raises(InvalidTimeWindowError, match="Month must be an integer"):
        ReportingPeriod.for_month(year=2026, month="2", timezone="Europe/Prague")  # type: ignore[arg-type]


def test_reporting_period_rejects_non_integer_year() -> None:
    """Reject non-integer year values."""
    with pytest.raises(InvalidTimeWindowError, match="Year must be an integer"):
        ReportingPeriod.for_month(year="2026", month=2, timezone="Europe/Prague")  # type: ignore[arg-type]


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


def test_reporting_period_rejects_direct_instantiation_with_end_before_start() -> None:
    """Reject direct construction where end is not after start."""
    with pytest.raises(InvalidTimeWindowError, match="end must be after start"):
        ReportingPeriod(
            year=2026,
            month=2,
            start_datetime=datetime(2026, 2, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2026, 2, 1, tzinfo=ZoneInfo("UTC")),
            timezone="UTC",
        )


def test_reporting_period_rejects_timezone_mismatch_in_direct_instantiation() -> None:
    """Reject direct construction with datetime timezone mismatch."""
    with pytest.raises(
        InvalidTimeWindowError,
        match="datetimes must use the configured timezone",
    ):
        ReportingPeriod(
            year=2026,
            month=2,
            start_datetime=datetime(2026, 2, 1, tzinfo=ZoneInfo("UTC")),
            end_datetime=datetime(2026, 3, 1, tzinfo=ZoneInfo("UTC")),
            timezone="Europe/Prague",
        )


def test_reporting_period_from_time_window_rejects_missing_fields() -> None:
    """Reject TimeWindow-like payloads missing year or month attributes."""

    class MissingWindow:
        pass

    with pytest.raises(InvalidTimeWindowError, match="Time window must include year and month"):
        ReportingPeriod.from_time_window(window=MissingWindow(), timezone="Europe/Prague")
