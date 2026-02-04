"""Aggregate dashboard data from stored submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import (
    OverviewDashboardData,
    TeamDetailDashboardData,
    TeamMonthlySnapshot,
    TeamOverviewCard,
    TrendsDashboardData,
    TrendSeries,
)

if TYPE_CHECKING:
    from qa_chatbot.application.ports import StoragePort
    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, Submission, TeamId, TimeWindow


@dataclass(frozen=True)
class GetDashboardDataUseCase:
    """Provide aggregated data for dashboard views."""

    storage_port: StoragePort

    def build_overview(self, month: TimeWindow) -> OverviewDashboardData:
        """Build overview data for a reporting month."""
        submissions = self.storage_port.get_submissions_by_month(month)
        teams = [self._to_overview_card(submission) for submission in submissions]
        teams.sort(key=lambda card: card.team_id.value)
        return OverviewDashboardData(month=month, teams=teams)

    def build_team_detail(self, team_id: TeamId, months: list[TimeWindow]) -> TeamDetailDashboardData:
        """Build detail data for a team across months."""
        snapshots: list[TeamMonthlySnapshot] = []
        for month in months:
            submissions = self.storage_port.get_submissions_by_team(team_id, month)
            if not submissions:
                snapshots.append(self._empty_snapshot(month))
                continue
            latest = self._latest_submission(submissions)
            snapshots.append(self._to_snapshot(latest))
        return TeamDetailDashboardData(team_id=team_id, snapshots=snapshots)

    def build_trends(self, teams: list[TeamId], months: list[TimeWindow]) -> TrendsDashboardData:
        """Build trends data for teams across months."""
        qa_metric_series = {
            "tests_passed": self._trend_series(teams, months, "qa_metrics", "tests_passed"),
            "tests_failed": self._trend_series(teams, months, "qa_metrics", "tests_failed"),
            "test_coverage_percent": self._trend_series(
                teams,
                months,
                "qa_metrics",
                "test_coverage_percent",
            ),
            "bug_count": self._trend_series(teams, months, "qa_metrics", "bug_count"),
            "critical_bugs": self._trend_series(teams, months, "qa_metrics", "critical_bugs"),
        }
        project_metric_series = {
            "sprint_progress_percent": self._trend_series(
                teams,
                months,
                "project_status",
                "sprint_progress_percent",
            ),
        }
        return TrendsDashboardData(
            teams=teams,
            months=months,
            qa_metric_series=qa_metric_series,
            project_metric_series=project_metric_series,
        )

    def _trend_series(
        self,
        teams: list[TeamId],
        months: list[TimeWindow],
        section: str,
        field: str,
    ) -> list[TrendSeries]:
        series: list[TrendSeries] = []
        for team in teams:
            values: list[float | int | None] = []
            for month in months:
                submissions = self.storage_port.get_submissions_by_team(team, month)
                if not submissions:
                    values.append(None)
                    continue
                latest = self._latest_submission(submissions)
                value = self._extract_section_value(latest, section, field)
                values.append(value)
            series.append(TrendSeries(label=team.value, values=values))
        return series

    def _extract_section_value(
        self,
        submission: Submission,
        section: str,
        field: str,
    ) -> float | int | None:
        section_value = getattr(submission, section)
        if section_value is None:
            return None
        return getattr(section_value, field, None)

    def _latest_submission(self, submissions: list[Submission]) -> Submission:
        return max(submissions, key=lambda item: item.created_at)

    def _to_overview_card(self, submission: Submission) -> TeamOverviewCard:
        return TeamOverviewCard(
            team_id=submission.team_id,
            month=submission.month,
            qa_metrics=self._metrics_payload(submission.qa_metrics),
            project_status=self._project_payload(submission.project_status),
            daily_update=self._daily_payload(submission.daily_update),
        )

    def _to_snapshot(self, submission: Submission) -> TeamMonthlySnapshot:
        return TeamMonthlySnapshot(
            month=submission.month,
            qa_metrics=self._metrics_payload(submission.qa_metrics),
            project_status=self._project_payload(submission.project_status),
            daily_update=self._daily_payload(submission.daily_update),
        )

    def _empty_snapshot(self, month: TimeWindow) -> TeamMonthlySnapshot:
        return TeamMonthlySnapshot(
            month=month,
            qa_metrics=self._metrics_payload(None),
            project_status=self._project_payload(None),
            daily_update=self._daily_payload(None),
        )

    def _metrics_payload(self, metrics: QAMetrics | None) -> dict[str, float | int | bool | None]:
        if metrics is None:
            return {
                "tests_passed": None,
                "tests_failed": None,
                "test_coverage_percent": None,
                "bug_count": None,
                "critical_bugs": None,
                "deployment_ready": None,
            }
        return {
            "tests_passed": metrics.tests_passed,
            "tests_failed": metrics.tests_failed,
            "test_coverage_percent": metrics.test_coverage_percent,
            "bug_count": metrics.bug_count,
            "critical_bugs": metrics.critical_bugs,
            "deployment_ready": metrics.deployment_ready,
        }

    def _project_payload(self, status: ProjectStatus | None) -> dict[str, float | list[str] | None]:
        if status is None:
            return {
                "sprint_progress_percent": None,
                "blockers": [],
                "milestones_completed": [],
                "risks": [],
            }
        return {
            "sprint_progress_percent": status.sprint_progress_percent,
            "blockers": list(status.blockers),
            "milestones_completed": list(status.milestones_completed),
            "risks": list(status.risks),
        }

    def _daily_payload(self, update: DailyUpdate | None) -> dict[str, float | list[str] | None]:
        if update is None:
            return {
                "completed_tasks": [],
                "planned_tasks": [],
                "capacity_hours": None,
                "issues": [],
            }
        return {
            "completed_tasks": list(update.completed_tasks),
            "planned_tasks": list(update.planned_tasks),
            "capacity_hours": update.capacity_hours,
            "issues": list(update.issues),
        }
