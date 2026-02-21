"""Unit tests for submission persistence orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import SubmissionCommand
from qa_chatbot.application.use_cases import SubmitProjectDataUseCase
from qa_chatbot.domain import DomainError, ProjectId, Submission, SubmissionMetrics, TestCoverageMetrics, TimeWindow

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture

EXPECTED_MERGED_MANUAL_TOTAL = 8
EXPECTED_MERGED_AUTOMATED_TOTAL = 7
EXPECTED_MERGED_RELEASES_COUNT = 2


@dataclass
class _FakeStoragePort:
    """In-memory storage fake for submission tests."""

    submissions: list[Submission] = field(default_factory=list)

    def save_submission(self, submission: Submission) -> None:
        self.submissions.append(submission)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        return [submission for submission in self.submissions if submission.project_id == project_id and submission.month == month]

    def get_all_projects(self) -> list[ProjectId]:
        return sorted({submission.project_id for submission in self.submissions}, key=lambda project: project.value)

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        return [submission for submission in self.submissions if submission.month == month]

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        months = sorted({submission.month for submission in self.submissions}, key=lambda item: item.to_iso_month())
        return list(reversed(months))[:limit]

    def get_overall_test_cases_by_month(self, month: TimeWindow) -> int | None:
        _ = month
        return None


@dataclass
class _FakeMetricsPort:
    """Collect submission metrics calls."""

    calls: list[tuple[ProjectId, TimeWindow]] = field(default_factory=list)

    def record_submission(self, project_id: ProjectId, time_window: TimeWindow) -> None:
        self.calls.append((project_id, time_window))

    def record_llm_latency(self, operation: str, elapsed_ms: float) -> None:
        _ = operation
        _ = elapsed_ms


@dataclass
class _FailingOverviewDashboardPort:
    """Dashboard fake that fails for overview generation only."""

    detail_calls: int = 0
    trends_calls: int = 0

    def generate_overview(self, month: TimeWindow) -> Path:
        _ = month
        msg = "overview failed"
        raise DomainError(msg)

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        _ = project_id
        _ = months
        self.detail_calls += 1
        return Path("project.html")

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        _ = projects
        _ = months
        self.trends_calls += 1
        return Path("trends.html")


def _coverage(*, manual_total: int | None, automated_total: int | None) -> TestCoverageMetrics:
    return TestCoverageMetrics(
        manual_total=manual_total,
        automated_total=automated_total,
        manual_created_in_reporting_month=None,
        manual_updated_in_reporting_month=None,
        automated_created_in_reporting_month=None,
        automated_updated_in_reporting_month=None,
    )


def _command(
    *,
    project_id: ProjectId,
    month: TimeWindow,
    manual_total: int | None,
    automated_total: int | None,
    correlation_id: str | None = None,
) -> SubmissionCommand:
    return SubmissionCommand(
        project_id=project_id,
        time_window=month,
        metrics=SubmissionMetrics(
            test_coverage=_coverage(manual_total=manual_total, automated_total=automated_total),
            overall_test_cases=None,
            supported_releases_count=None,
        ),
        raw_conversation="test",
        created_at=datetime(2026, 1, 2, tzinfo=UTC),
        correlation_id=correlation_id,
    )


def test_execute_merges_with_existing_submission() -> None:
    """Fill missing incoming fields from the latest existing submission."""
    month = TimeWindow.from_year_month(2026, 1)
    project_id = ProjectId("project-a")
    existing_submission = Submission.create(
        project_id=project_id,
        month=month,
        metrics=SubmissionMetrics(
            test_coverage=_coverage(manual_total=8, automated_total=4),
            overall_test_cases=None,
            supported_releases_count=2,
        ),
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
    )
    storage = _FakeStoragePort(submissions=[existing_submission])
    use_case = SubmitProjectDataUseCase(storage_port=storage)

    result = use_case.execute(
        _command(
            project_id=project_id,
            month=month,
            manual_total=None,
            automated_total=7,
        )
    )

    assert result.submission.metrics.test_coverage is not None
    assert result.submission.metrics.test_coverage.manual_total == EXPECTED_MERGED_MANUAL_TOTAL
    assert result.submission.metrics.test_coverage.automated_total == EXPECTED_MERGED_AUTOMATED_TOTAL
    assert result.submission.metrics.supported_releases_count == EXPECTED_MERGED_RELEASES_COUNT
    assert result.warnings == ()


def test_execute_survives_dashboard_generation_failure(caplog: LogCaptureFixture) -> None:
    """Persist submission even when one dashboard view fails."""
    month = TimeWindow.from_year_month(2026, 1)
    project_id = ProjectId("project-a")
    storage = _FakeStoragePort()
    dashboard = _FailingOverviewDashboardPort()
    metrics = _FakeMetricsPort()
    use_case = SubmitProjectDataUseCase(
        storage_port=storage,
        dashboard_port=dashboard,
        metrics_port=metrics,
    )

    logger_name = "qa_chatbot.application.use_cases.submit_project_data"
    with caplog.at_level(logging.INFO, logger=logger_name):
        result = use_case.execute(
            _command(
                project_id=project_id,
                month=month,
                manual_total=3,
                automated_total=5,
                correlation_id="session-123",
            )
        )

    assert result.submission in storage.submissions
    assert metrics.calls == [(project_id, month)]
    assert dashboard.detail_calls == 1
    assert dashboard.trends_calls == 1
    assert len(result.warnings) == 1
    assert "overview failed" in result.warnings[0]

    submit_record = next(record for record in caplog.records if record.getMessage() == "Submitting project data")
    saved_record = next(record for record in caplog.records if record.getMessage() == "Submission saved")
    dashboard_error_record = next(record for record in caplog.records if record.getMessage() == "Dashboard generation failed")

    assert getattr(submit_record, "correlation_id", None) == "session-123"
    assert getattr(saved_record, "correlation_id", None) == "session-123"
    assert getattr(dashboard_error_record, "correlation_id", None) == "session-123"
