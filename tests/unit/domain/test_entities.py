"""Unit tests for domain entities."""

from datetime import UTC, datetime

import pytest

from qa_chatbot.domain import (
    DailyUpdate,
    InvalidSubmissionTeamError,
    MissingSubmissionDataError,
    Submission,
    TeamData,
    TeamId,
    TimeWindow,
)


def test_submission_requires_data(team_id_a: TeamId, time_window_jan: TimeWindow) -> None:
    """Raise when no submission data is provided."""
    with pytest.raises(MissingSubmissionDataError):
        Submission.create(
            team_id=team_id_a,
            month=time_window_jan,
            qa_metrics=None,
            project_status=None,
            daily_update=None,
        )


def test_submission_create_sets_defaults(
    team_id_a: TeamId,
    time_window_jan: TimeWindow,
    daily_update_done: DailyUpdate,
) -> None:
    """Populate missing submission defaults."""
    submission = Submission.create(
        team_id=team_id_a,
        month=time_window_jan,
        qa_metrics=None,
        project_status=None,
        daily_update=daily_update_done,
        created_at=datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC),
    )

    assert submission.id is not None
    assert submission.created_at == datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)


def test_team_data_rejects_wrong_team_submission(
    team_id_a: TeamId,
    team_id_b: TeamId,
    time_window_jan: TimeWindow,
    daily_update_done: DailyUpdate,
) -> None:
    """Reject submissions from a different team."""
    team_data = TeamData(team_id=team_id_a)
    submission = Submission.create(
        team_id=team_id_b,
        month=time_window_jan,
        qa_metrics=None,
        project_status=None,
        daily_update=daily_update_done,
    )

    with pytest.raises(InvalidSubmissionTeamError):
        team_data.add_submission(submission)


def test_team_data_filters_submissions_for_month(
    team_id_a: TeamId,
    time_window_jan: TimeWindow,
    time_window_feb: TimeWindow,
    daily_update_done: DailyUpdate,
) -> None:
    """Return only submissions for the requested month."""
    team_data = TeamData(team_id=team_id_a)
    january_submission = Submission.create(
        team_id=team_id_a,
        month=time_window_jan,
        qa_metrics=None,
        project_status=None,
        daily_update=daily_update_done,
    )
    february_submission = Submission.create(
        team_id=team_id_a,
        month=time_window_feb,
        qa_metrics=None,
        project_status=None,
        daily_update=daily_update_done,
    )

    team_data.add_submission(january_submission)
    team_data.add_submission(february_submission)

    assert team_data.submissions_for_month(time_window_jan) == [january_submission]
