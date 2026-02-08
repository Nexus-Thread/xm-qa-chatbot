"""Unit tests for domain entities."""

from datetime import UTC, datetime

import pytest

from qa_chatbot.domain import (
    InvalidSubmissionTeamError,
    ProjectId,
    Submission,
    TeamData,
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


def test_team_data_rejects_wrong_team_submission(
    project_id_a: ProjectId,
    project_id_b: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Reject submissions from a different team."""
    team_data = TeamData(project_id=project_id_a)
    submission = Submission.create(
        project_id=project_id_b,
        month=time_window_jan,
        test_coverage=test_coverage_done,
        overall_test_cases=None,
    )

    with pytest.raises(InvalidSubmissionTeamError):
        team_data.add_submission(submission)


def test_team_data_filters_submissions_for_month(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    time_window_feb: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Return only submissions for the requested month."""
    team_data = TeamData(project_id=project_id_a)
    january_submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=test_coverage_done,
        overall_test_cases=None,
    )
    february_submission = Submission.create(
        project_id=project_id_a,
        month=time_window_feb,
        test_coverage=test_coverage_done,
        overall_test_cases=None,
    )

    team_data.add_submission(january_submission)
    team_data.add_submission(february_submission)

    assert team_data.submissions_for_month(time_window_jan) == [january_submission]
