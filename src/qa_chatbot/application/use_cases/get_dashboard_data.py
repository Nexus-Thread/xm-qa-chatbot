"""Aggregate dashboard data from stored submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import (
    OverviewDashboardData,
    ProjectDetailDashboardData,
    ProjectMonthlySnapshot,
    ProjectOverviewCard,
    TrendsDashboardData,
    TrendSeries,
)

if TYPE_CHECKING:
    from qa_chatbot.application.ports import StoragePort
    from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow


@dataclass(frozen=True)
class GetDashboardDataUseCase:
    """Provide aggregated data for dashboard views."""

    storage_port: StoragePort

    def build_overview(self, month: TimeWindow) -> OverviewDashboardData:
        """Build overview data for a reporting month."""
        submissions = self.storage_port.get_submissions_by_month(month)
        projects = [self._to_overview_card(submission) for submission in submissions]
        projects.sort(key=lambda card: card.project_id.value)
        return OverviewDashboardData(month=month, projects=projects)

    def build_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> ProjectDetailDashboardData:
        """Build detail data for a project across months."""
        snapshots: list[ProjectMonthlySnapshot] = []
        for month in months:
            submissions = self.storage_port.get_submissions_by_project(project_id, month)
            if not submissions:
                snapshots.append(self._empty_snapshot(month))
                continue
            latest = self._latest_submission(submissions)
            snapshots.append(self._to_snapshot(latest))
        return ProjectDetailDashboardData(project_id=project_id, snapshots=snapshots)

    def build_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> TrendsDashboardData:
        """Build trends data for projects across months."""
        qa_metric_series = {
            "manual_total": self._trend_series(projects, months, "test_coverage", "manual_total"),
            "automated_total": self._trend_series(projects, months, "test_coverage", "automated_total"),
            "percentage_automation": self._trend_series(projects, months, "test_coverage", "percentage_automation"),
        }
        return TrendsDashboardData(
            projects=projects,
            months=months,
            qa_metric_series=qa_metric_series,
            project_metric_series={},
        )

    def _trend_series(
        self,
        projects: list[ProjectId],
        months: list[TimeWindow],
        section: str,
        field: str,
    ) -> list[TrendSeries]:
        series: list[TrendSeries] = []
        for project in projects:
            values: list[float | int | None] = []
            for month in months:
                submissions = self.storage_port.get_submissions_by_project(project, month)
                if not submissions:
                    values.append(None)
                    continue
                latest = self._latest_submission(submissions)
                value = self._extract_section_value(latest, section, field)
                values.append(value)
            series.append(TrendSeries(label=project.value, values=values))
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

    def _to_overview_card(self, submission: Submission) -> ProjectOverviewCard:
        return ProjectOverviewCard(
            project_id=submission.project_id,
            month=submission.month,
            qa_metrics=self._coverage_payload(submission.test_coverage),
            project_status={},
            daily_update={},
        )

    def _to_snapshot(self, submission: Submission) -> ProjectMonthlySnapshot:
        return ProjectMonthlySnapshot(
            month=submission.month,
            qa_metrics=self._coverage_payload(submission.test_coverage),
            project_status={},
            daily_update={},
        )

    def _empty_snapshot(self, month: TimeWindow) -> ProjectMonthlySnapshot:
        return ProjectMonthlySnapshot(
            month=month,
            qa_metrics=self._coverage_payload(None),
            project_status={},
            daily_update={},
        )

    def _coverage_payload(self, metrics: TestCoverageMetrics | None) -> dict[str, float | int | bool | None]:
        if metrics is None:
            return {
                "manual_total": None,
                "automated_total": None,
                "manual_created_in_reporting_month": None,
                "manual_updated_in_reporting_month": None,
                "automated_created_in_reporting_month": None,
                "automated_updated_in_reporting_month": None,
                "percentage_automation": None,
            }
        return {
            "manual_total": metrics.manual_total,
            "automated_total": metrics.automated_total,
            "manual_created_in_reporting_month": metrics.manual_created_in_reporting_month,
            "manual_updated_in_reporting_month": metrics.manual_updated_in_reporting_month,
            "automated_created_in_reporting_month": metrics.automated_created_in_reporting_month,
            "automated_updated_in_reporting_month": metrics.automated_updated_in_reporting_month,
            "percentage_automation": metrics.percentage_automation,
        }
