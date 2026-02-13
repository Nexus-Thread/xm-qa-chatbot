"""Integration tests for SQLite adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
    from qa_chatbot.domain import ProjectId, Submission, TimeWindow

# Test data constants
INITIAL_MANUAL_TOTAL = 10
UPDATED_MANUAL_TOTAL = 2000
UPDATED_AUTOMATED_TOTAL = 500


def test_sqlite_adapter_persists_and_queries(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Persist and query submissions through the adapter."""
    sqlite_adapter.save_submission(submission_project_a_jan)

    by_team = sqlite_adapter.get_submissions_by_project(project_id_a, time_window_jan)
    by_month = sqlite_adapter.get_submissions_by_month(time_window_jan)
    teams = sqlite_adapter.get_all_projects()

    assert len(by_team) == 1
    assert by_team[0].project_id == project_id_a
    assert len(by_month) == 1
    assert teams == [project_id_a]


def test_sqlite_adapter_resubmission_replaces_data(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Resubmitting data for same project/month replaces the previous submission."""
    from qa_chatbot.domain import Submission, TestCoverageMetrics  # noqa: PLC0415

    # Submit initial data
    sqlite_adapter.save_submission(submission_project_a_jan)

    # Verify initial submission
    submissions = sqlite_adapter.get_submissions_by_project(project_id_a, time_window_jan)
    assert len(submissions) == 1
    initial_coverage = submissions[0].test_coverage
    assert initial_coverage is not None
    assert initial_coverage.manual_total == INITIAL_MANUAL_TOTAL

    # Resubmit with different data for same project/month
    updated_coverage = TestCoverageMetrics(
        manual_total=2000,  # Changed from 1000
        automated_total=500,  # Changed from 0
        manual_created_in_reporting_month=50,
        manual_updated_in_reporting_month=60,
        automated_created_in_reporting_month=25,
        automated_updated_in_reporting_month=30,
        percentage_automation=20.0,
    )
    resubmission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=updated_coverage,
        overall_test_cases=None,
        raw_conversation="Updated data",
    )
    sqlite_adapter.save_submission(resubmission)

    # Verify only one submission exists with updated data
    submissions_after = sqlite_adapter.get_submissions_by_project(project_id_a, time_window_jan)
    assert len(submissions_after) == 1, "Should have only one submission after resubmission"

    updated = submissions_after[0]
    assert updated.test_coverage is not None
    assert updated.test_coverage.manual_total == UPDATED_MANUAL_TOTAL, "Manual total should be updated"
    assert updated.test_coverage.automated_total == UPDATED_AUTOMATED_TOTAL, "Automated total should be updated"
    assert updated.raw_conversation == "Updated data"
