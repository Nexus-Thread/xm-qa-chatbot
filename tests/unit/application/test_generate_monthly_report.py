"""Unit tests for monthly report generation edge cases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, cast

import pytest

from qa_chatbot.application.services import EdgeCasePolicy
from qa_chatbot.application.use_cases import GenerateMonthlyReportUseCase
from qa_chatbot.domain import (
    BucketCount,
    BusinessStream,
    DefectLeakage,
    InvalidConfigurationError,
    Project,
    ProjectId,
    StreamId,
    StreamProjectRegistry,
    Submission,
    TestCoverageMetrics,
    TimeWindow,
)

if TYPE_CHECKING:
    from qa_chatbot.domain.entities import ReportingPeriod


@dataclass(frozen=True)
class _BrokenLeakage:
    """Defect leakage payload used to simulate malformed adapter output."""

    rate_percent: float


class _FakeStoragePort:
    """In-memory storage for monthly report tests."""

    def __init__(self, submissions: list[Submission]) -> None:
        self._submissions = submissions

    def save_submission(self, submission: Submission) -> None:
        self._submissions.append(submission)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        return [submission for submission in self._submissions if submission.project_id == project_id and submission.month == month]

    def get_all_projects(self) -> list[ProjectId]:
        projects = {submission.project_id for submission in self._submissions}
        return sorted(projects, key=lambda project: project.value)

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        return [submission for submission in self._submissions if submission.month == month]

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        months = sorted({submission.month for submission in self._submissions}, key=lambda item: item.to_iso_month())
        return list(reversed(months))[:limit]


class _FakeJiraPort:
    """Jira metrics stub for monthly report tests."""

    def __init__(self, *, return_non_finite_fallback: bool = False) -> None:
        self._return_non_finite_fallback = return_non_finite_fallback

    def fetch_bugs_found(self, project_id: ProjectId, _period: ReportingPeriod) -> BucketCount:
        del project_id
        return BucketCount(p1_p2=1, p3_p4=0)

    def fetch_production_incidents(self, project_id: ProjectId, _period: ReportingPeriod) -> BucketCount:
        del project_id
        return BucketCount(p1_p2=0, p3_p4=1)

    def fetch_defect_leakage(self, project_id: ProjectId, _period: ReportingPeriod) -> DefectLeakage:
        del project_id
        if self._return_non_finite_fallback:
            return cast("DefectLeakage", _BrokenLeakage(rate_percent=float("nan")))
        return DefectLeakage(numerator=0, denominator=0, rate_percent=0.0)

    def build_issue_link(self, project_id: ProjectId, _period: ReportingPeriod, label: str) -> str:
        return f"https://jira.example.com/{project_id.value}/{label}"


def _build_registry() -> StreamProjectRegistry:
    stream = BusinessStream(id=StreamId("stream-a"), name="Stream A", order=0)
    project = Project(id="project-a", name="Project A", business_stream_id=stream.id)
    return StreamProjectRegistry(streams=(stream,), projects=(project,))


def _submission(month: TimeWindow) -> Submission:
    return Submission.create(
        project_id=ProjectId("project-a"),
        month=month,
        test_coverage=TestCoverageMetrics(
            manual_total=0,
            automated_total=0,
            manual_created_in_reporting_month=0,
            manual_updated_in_reporting_month=0,
            automated_created_in_reporting_month=0,
            automated_updated_in_reporting_month=0,
        ),
        overall_test_cases=None,
        created_at=datetime(2026, 1, 10, tzinfo=UTC),
    )


def test_execute_uses_none_for_zero_denominator_percentages() -> None:
    """Return None for zero-denominator percentages without breaking report generation."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=[_submission(month)]),
        jira_port=_FakeJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    report = use_case.execute(month)

    assert report.test_coverage_rows[0].percentage_automation is None
    assert report.quality_metrics_rows[1].defect_leakage.rate_percent is None
    assert report.quality_metrics_rows[0].defect_leakage.rate_percent == 0.0


def test_execute_sanitizes_non_finite_fallback_leakage_rate() -> None:
    """Treat malformed non-finite fallback leakage rates as missing."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=[_submission(month)]),
        jira_port=_FakeJiraPort(return_non_finite_fallback=True),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    report = use_case.execute(month)

    assert report.quality_metrics_rows[1].defect_leakage.rate_percent is None
    assert report.quality_metrics_rows[0].defect_leakage.rate_percent == 0.0


def test_init_raises_for_invalid_completeness_mode() -> None:
    """Reject unsupported completeness mode configuration."""
    month = TimeWindow.from_year_month(2026, 1)

    with pytest.raises(InvalidConfigurationError):
        GenerateMonthlyReportUseCase(
            storage_port=_FakeStoragePort(submissions=[_submission(month)]),
            jira_port=_FakeJiraPort(),
            registry=_build_registry(),
            timezone="UTC",
            edge_case_policy=EdgeCasePolicy(),
            completeness_mode="unknown",
        )
