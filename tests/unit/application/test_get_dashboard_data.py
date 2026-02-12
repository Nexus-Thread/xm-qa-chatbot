"""Tests for dashboard data aggregation."""

from __future__ import annotations

from datetime import UTC, datetime

from qa_chatbot.application.use_cases import GetDashboardDataUseCase
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow

# Test data constants
EXPECTED_MANUAL_TOTAL = 8


class FakeStoragePort:
    """In-memory storage port for dashboard tests."""

    def __init__(self, submissions: list[Submission]) -> None:
        """Store submissions for queries."""
        self._submissions = submissions

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission in memory."""
        self._submissions.append(submission)

    def get_submissions_by_project(self, team_id: ProjectId, month: TimeWindow) -> list[Submission]:
        """Return submissions for a project and month."""
        return [submission for submission in self._submissions if submission.project_id == team_id and submission.month == month]

    def get_all_projects(self) -> list[ProjectId]:
        """Return all project IDs in sorted order."""
        return sorted({submission.project_id for submission in self._submissions}, key=lambda team: team.value)

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a reporting month."""
        return [submission for submission in self._submissions if submission.month == month]

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return recent months in descending order."""
        months = sorted({submission.month for submission in self._submissions}, key=lambda item: item.to_iso_month())
        return list(reversed(months))[:limit]


def _submission(
    project_id: ProjectId,
    month: TimeWindow,
    *,
    manual_total: int,
    created_at: datetime,
) -> Submission:
    """Create a submission with standard fields for testing."""
    return Submission.create(
        project_id=project_id,
        month=month,
        test_coverage=TestCoverageMetrics(
            manual_total=manual_total,
            automated_total=5,
            manual_created_last_month=1,
            manual_updated_last_month=1,
            automated_created_last_month=1,
            automated_updated_last_month=1,
            percentage_automation=33.33,
        ),
        overall_test_cases=None,
        created_at=created_at,
    )


def test_build_overview_sorts_by_team() -> None:
    """Ensure overview cards are sorted by team ID."""
    team_a = ProjectId("Alpha")
    team_b = ProjectId("Beta")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team_b, month, manual_total=10, created_at=datetime(2026, 1, 5, tzinfo=UTC)),
        _submission(team_a, month, manual_total=5, created_at=datetime(2026, 1, 4, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    overview = use_case.build_overview(month)

    assert [card.team_id.value for card in overview.teams] == ["Alpha", "Beta"]


def test_build_team_detail_prefers_latest_submission() -> None:
    """Ensure team detail chooses the most recent submission."""
    team = ProjectId("Gamma")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team, month, manual_total=3, created_at=datetime(2026, 1, 3, tzinfo=UTC)),
        _submission(team, month, manual_total=8, created_at=datetime(2026, 1, 10, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    detail = use_case.build_team_detail(team, [month])

    assert detail.snapshots[0].qa_metrics["manual_total"] == EXPECTED_MANUAL_TOTAL


def test_build_trends_returns_series_for_each_team() -> None:
    """Ensure trend series includes each team."""
    team_a = ProjectId("Alpha")
    team_b = ProjectId("Beta")
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        _submission(team_a, month, manual_total=4, created_at=datetime(2026, 1, 2, tzinfo=UTC)),
        _submission(team_b, month, manual_total=9, created_at=datetime(2026, 1, 2, tzinfo=UTC)),
    ]
    use_case = GetDashboardDataUseCase(storage_port=FakeStoragePort(submissions))

    trends = use_case.build_trends([team_a, team_b], [month])

    series_labels = [series.label for series in trends.qa_metric_series["manual_total"]]
    assert series_labels == ["Alpha", "Beta"]
