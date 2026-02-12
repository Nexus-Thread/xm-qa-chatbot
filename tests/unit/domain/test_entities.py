"""Unit tests for domain entities."""

from datetime import UTC, datetime

from qa_chatbot.domain import (
    ProjectId,
    Submission,
    TestCoverageMetrics,
    TimeWindow,
)


def test_submission_allows_partial_data(project_id_a: ProjectId, time_window_jan: TimeWindow) -> None:
    """Allow partial submissions without coverage data."""
    submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=None,
        overall_test_cases=None,
    )

    assert submission.test_coverage is None


def test_submission_create_sets_defaults(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> None:
    """Populate missing submission defaults."""
    submission = Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=test_coverage_done,
        overall_test_cases=None,
        created_at=datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC),
    )

    assert submission.id is not None
    assert submission.created_at == datetime(2026, 1, 31, 12, 0, 0, tzinfo=UTC)
