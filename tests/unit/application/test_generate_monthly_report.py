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


class _OperationalFailingJiraPort(_FakeJiraPort):
    """Jira stub that simulates operational upstream failures for one metric."""

    def fetch_bugs_found(self, project_id: ProjectId, _period: ReportingPeriod) -> BucketCount:
        del project_id
        msg = "jira unavailable"
        raise ConnectionError(msg)


class _ProgrammingErrorJiraPort(_FakeJiraPort):
    """Jira stub that simulates a programming bug in adapter code."""

    def fetch_bugs_found(self, project_id: ProjectId, _period: ReportingPeriod) -> BucketCount:
        del project_id
        msg = "unexpected adapter attribute mismatch"
        raise AttributeError(msg)


class _PartialCoverageStoragePort(_FakeStoragePort):
    """Storage stub returning partial coverage data by project."""

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        submissions = super().get_submissions_by_project(project_id, month)
        if project_id.value == "project-a":
            return [
                Submission.create(
                    project_id=project_id,
                    month=month,
                    test_coverage=TestCoverageMetrics(manual_total=None, automated_total=2),
                    overall_test_cases=None,
                    created_at=datetime(2026, 1, 12, tzinfo=UTC),
                ),
            ]
        return submissions


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


def test_execute_marks_failed_completeness_in_fail_mode() -> None:
    """Mark report as failed completeness when configured to fail on missing data."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=[]),
        jira_port=_FakeJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
        completeness_mode="fail",
    )

    report = use_case.execute(month)

    assert report.completeness.status == "FAILED"
    assert "test_coverage:project-a" in report.completeness.missing


def test_execute_handles_jira_fetch_errors_as_missing_data() -> None:
    """Capture operational Jira fetch errors as missing metrics instead of failing report generation."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=[_submission(month)]),
        jira_port=_OperationalFailingJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    report = use_case.execute(month)

    assert report.completeness.status == "PARTIAL"
    assert "bugs_found:project-a" in report.completeness.missing
    assert report.quality_metrics_rows[1].bugs_found.p1_p2 is None
    assert report.quality_metrics_rows[1].bugs_found.p3_p4 is None


def test_execute_propagates_programming_errors_from_jira_fetch() -> None:
    """Propagate programming errors from Jira fetch instead of masking them as missing data."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=[_submission(month)]),
        jira_port=_ProgrammingErrorJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    with pytest.raises(AttributeError):
        _ = use_case.execute(month)


def test_execute_returns_none_for_automation_percentage_when_totals_are_partial() -> None:
    """Return None automation percentage when one of the totals is missing."""
    month = TimeWindow.from_year_month(2026, 1)
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_PartialCoverageStoragePort(submissions=[_submission(month)]),
        jira_port=_FakeJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    report = use_case.execute(month)

    assert report.test_coverage_rows[0].percentage_automation is None


def test_execute_returns_none_overall_test_cases_when_no_complete_totals_exist() -> None:
    """Return None for overall test cases when monthly submissions lack complete coverage totals."""
    month = TimeWindow.from_year_month(2026, 1)
    submissions = [
        Submission.create(
            project_id=ProjectId("project-a"),
            month=month,
            test_coverage=None,
            overall_test_cases=None,
            supported_releases_count=1,
            created_at=datetime(2026, 1, 8, tzinfo=UTC),
        ),
    ]
    use_case = GenerateMonthlyReportUseCase(
        storage_port=_FakeStoragePort(submissions=submissions),
        jira_port=_FakeJiraPort(),
        registry=_build_registry(),
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
    )

    report = use_case.execute(month)

    assert report.overall_test_cases is None
