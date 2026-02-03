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


def test_submission_requires_data() -> None:
    """Raise when no submission data is provided."""
    with pytest.raises(MissingSubmissionDataError):
        Submission.create(
            team_id=TeamId("Team A"),
            month=TimeWindow.from_year_month(2026, 1),
            qa_metrics=None,
            project_status=None,
            daily_update=None,
        )


def test_submission_create_sets_defaults() -> None:
    """Populate missing submission defaults."""
    submission = Submission.create(
        team_id=TeamId("Team A"),
        month=TimeWindow.from_year_month(2026, 1),
        qa_metrics=None,
        project_status=None,
        daily_update=DailyUpdate(completed_tasks=("Done",)),
        created_at=datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC),
    )

    assert submission.id is not None
    assert submission.created_at == datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)


def test_team_data_rejects_wrong_team_submission() -> None:
    """Reject submissions from a different team."""
    team_data = TeamData(team_id=TeamId("Team A"))
    submission = Submission.create(
        team_id=TeamId("Team B"),
        month=TimeWindow.from_year_month(2026, 1),
        qa_metrics=None,
        project_status=None,
        daily_update=DailyUpdate(completed_tasks=("Done",)),
    )

    with pytest.raises(InvalidSubmissionTeamError):
        team_data.add_submission(submission)
