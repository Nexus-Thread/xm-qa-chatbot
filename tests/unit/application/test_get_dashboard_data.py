"""Tests for dashboard data aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from qa_chatbot.application.use_cases import GetDashboardDataUseCase
from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, Submission, TeamId, TimeWindow


class FakeStoragePort:
    """In-memory storage port for dashboard tests."""

    def __init__(self, submissions: list[Submission]) -> None:
        """Store submissions for queries."""
        self._submissions = submissions

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission in memory."""
        self._submissions.append(submission)

    def get_submissions_by_team(self, team_id: TeamId, month: TimeWindow) -> list[Submission]:
        """Return submissions for a team and month."""
        return [
            submission
            for submission in self._submissions
            if submission.team_id == team_id and submission.month == month
        ]

    def get_all_teams(self) -> list[TeamId]:
        """Return all team IDs in sorted order."""
        return sorted({submission.team_id for submission in self._submissions}, key=lambda team: team.value)

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a reporting month."""
        return [submission for submission in self._submissions if submission.month == month]

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return recent months in descending order."""
        months = sorted({submission.month for submission in self._submissions}, key=lambda item: item.to_iso_month())
        return list(reversed(months))[:limit]


def _submission(
    team_id: TeamId,
    month: TimeWindow,
    *,
    tests_passed: int,
    created_at: datetime,
) -> Submission:
    """Create a submission with standard fields for testing."""
    return Submission.create(
        team_id=team_id,
        month=month,
        qa_metrics=QAMetrics(tests_passed=tests_passed, tests_failed=0),
        project_status=ProjectStatus(sprint_progress_percent=75.0, blockers=(), milestones_completed=(), risks=()),
        daily_update=DailyUpdate(completed_tasks=("Done",)),
        created_at=created_at,
    )


def test_build_overview_sorts_by_team() -> None:
    """Ensure overview cards are sorted by team ID."""
    team_a = TeamId("Alpha")
    team_b = TeamId("Beta")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team_b, month, tests_passed=10, created_at=datetime(2026, 1, 5, tzinfo=UTC)),
        _submission(team_a, month, tests_passed=5, created_at=datetime(2026, 1, 4, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    overview = use_case.build_overview(month)

    assert [card.team_id.value for card in overview.teams] == ["Alpha", "Beta"]


def test_build_team_detail_prefers_latest_submission() -> None:
    """Ensure team detail chooses the most recent submission."""
    team = TeamId("Gamma")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team, month, tests_passed=3, created_at=datetime(2026, 1, 3, tzinfo=UTC)),
        _submission(team, month, tests_passed=8, created_at=datetime(2026, 1, 10, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    detail = use_case.build_team_detail(team, [month])

    assert detail.snapshots[0].qa_metrics["tests_passed"] == 8


def test_build_trends_returns_series_for_each_team() -> None:
    """Ensure trend series includes each team."""
    team_a = TeamId("Alpha")
    team_b = TeamId("Beta")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team_a, month, tests_passed=4, created_at=datetime(2026, 1, 2, tzinfo=UTC)),
        _submission(team_b, month, tests_passed=9, created_at=datetime(2026, 1, 2, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    trends = use_case.build_trends([team_a, team_b], [month])

    series_labels = [series.label for series in trends.qa_metric_series["tests_passed"]]
    assert series_labels == ["Alpha", "Beta"]
