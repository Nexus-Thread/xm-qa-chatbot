"""Integration tests for SQLite adapter."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
from qa_chatbot.domain import StorageOperationError, Submission, TestCoverageMetrics

pytestmark = pytest.mark.integration

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.domain import ProjectId, TimeWindow

# Test data constants
INITIAL_MANUAL_TOTAL = 10
UPDATED_MANUAL_TOTAL = 2000
UPDATED_AUTOMATED_TOTAL = 500
EXPECTED_JANUARY_TOTAL = 25
EXPECTED_LATEST_ONLY_TOTAL = 17


def test_sqlite_adapter_persists_and_queries(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Persist and query submissions through the adapter."""
    sqlite_adapter.save_submission(submission_project_a_jan)

    by_project = sqlite_adapter.get_submissions_by_project(project_id_a, time_window_jan)
    by_month = sqlite_adapter.get_submissions_by_month(time_window_jan)
    projects = sqlite_adapter.get_all_projects()

    assert len(by_project) == 1
    assert by_project[0].project_id == project_id_a
    assert len(by_month) == 1
    assert projects == [project_id_a]


def test_sqlite_adapter_resubmission_replaces_data(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Resubmitting data for same project/month replaces the previous submission."""
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


def test_sqlite_adapter_returns_recent_months_descending_with_limit(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    project_id_b: ProjectId,
    time_window_feb: TimeWindow,
) -> None:
    """Return recent months in descending order and honor limit."""
    sqlite_adapter.save_submission(submission_project_a_jan)
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_b,
            month=time_window_feb,
            test_coverage=TestCoverageMetrics(manual_total=1, automated_total=1),
        )
    )

    recent_months = sqlite_adapter.get_recent_months(limit=1)

    assert [month.to_iso_month() for month in recent_months] == [time_window_feb.to_iso_month()]


def test_sqlite_adapter_aggregates_overall_test_cases_for_month(
    sqlite_adapter: SQLiteAdapter,
    project_id_a: ProjectId,
    project_id_b: ProjectId,
    time_window_jan: TimeWindow,
    time_window_feb: TimeWindow,
) -> None:
    """Aggregate overall test cases from all projects for a selected month."""
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=TestCoverageMetrics(manual_total=10, automated_total=5),
            created_at=datetime(2026, 1, 5, tzinfo=UTC),
        )
    )
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_b,
            month=time_window_jan,
            test_coverage=TestCoverageMetrics(manual_total=4, automated_total=6),
            created_at=datetime(2026, 1, 7, tzinfo=UTC),
        )
    )
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_a,
            month=time_window_feb,
            test_coverage=TestCoverageMetrics(manual_total=1, automated_total=1),
            created_at=datetime(2026, 2, 7, tzinfo=UTC),
        )
    )

    january_total = sqlite_adapter.get_overall_test_cases_by_month(time_window_jan)

    assert january_total == EXPECTED_JANUARY_TOTAL


def test_sqlite_adapter_aggregates_overall_test_cases_using_latest_submission(
    sqlite_adapter: SQLiteAdapter,
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
) -> None:
    """Use latest submission values when aggregating a project's monthly totals."""
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=TestCoverageMetrics(manual_total=1, automated_total=2),
            created_at=datetime(2026, 1, 2, tzinfo=UTC),
        )
    )
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=TestCoverageMetrics(manual_total=8, automated_total=9),
            created_at=datetime(2026, 1, 20, tzinfo=UTC),
        )
    )

    total = sqlite_adapter.get_overall_test_cases_by_month(time_window_jan)

    assert total == EXPECTED_LATEST_ONLY_TOTAL


def test_sqlite_adapter_returns_none_for_overall_test_cases_without_complete_coverage(
    sqlite_adapter: SQLiteAdapter,
    project_id_a: ProjectId,
    project_id_b: ProjectId,
    time_window_jan: TimeWindow,
    time_window_feb: TimeWindow,
) -> None:
    """Return None when no complete coverage totals are available for a month."""
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_a,
            month=time_window_jan,
            test_coverage=None,
            supported_releases_count=1,
            created_at=datetime(2026, 1, 5, tzinfo=UTC),
        )
    )
    sqlite_adapter.save_submission(
        Submission.create(
            project_id=project_id_b,
            month=time_window_jan,
            test_coverage=TestCoverageMetrics(manual_total=None, automated_total=6),
            created_at=datetime(2026, 1, 7, tzinfo=UTC),
        )
    )

    january_total = sqlite_adapter.get_overall_test_cases_by_month(time_window_jan)
    february_total = sqlite_adapter.get_overall_test_cases_by_month(time_window_feb)

    assert january_total is None
    assert february_total is None


def test_sqlite_adapter_clear_all_submissions_removes_data(
    sqlite_adapter: SQLiteAdapter,
    submission_project_a_jan: Submission,
    time_window_jan: TimeWindow,
) -> None:
    """Clear submissions removes all rows from storage."""
    sqlite_adapter.save_submission(submission_project_a_jan)

    sqlite_adapter.clear_all_submissions()

    assert sqlite_adapter.get_submissions_by_month(time_window_jan) == []
    assert sqlite_adapter.get_all_projects() == []


def test_sqlite_adapter_uses_integer_columns_for_scalar_metrics(sqlite_adapter: SQLiteAdapter) -> None:
    """Store scalar metrics as INTEGER columns in SQLite schema."""
    with sqlite_adapter.engine.connect() as connection:
        rows = connection.execute(text("PRAGMA table_info(submissions)"))
        table_info = {str(row[1]): str(row[2]) for row in rows}

    assert table_info["overall_test_cases"].upper() == "INTEGER"
    assert table_info["supported_releases_count"].upper() == "INTEGER"


def test_sqlite_adapter_translates_sqlalchemy_error(sqlite_adapter: SQLiteAdapter, time_window_jan: TimeWindow) -> None:
    """Translate SQLAlchemy read errors to domain storage errors."""
    with sqlite_adapter.engine.begin() as connection:
        connection.execute(text("DROP TABLE submissions"))

    with pytest.raises(StorageOperationError, match="SQLite read operation failed"):
        sqlite_adapter.get_submissions_by_month(time_window_jan)


def test_sqlite_adapter_initializes_wal_mode(sqlite_adapter: SQLiteAdapter) -> None:
    """Enable WAL journal mode when initializing SQLite schema."""
    with sqlite_adapter.engine.connect() as connection:
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()

    assert str(journal_mode).lower() == "wal"


def test_sqlite_adapter_applies_busy_timeout_from_configuration(tmp_path: Path) -> None:
    """Apply busy_timeout pragma from configured timeout seconds."""
    timeout_seconds = 12.5
    database_path = tmp_path / "busy_timeout.db"
    adapter = SQLiteAdapter(
        database_url=f"sqlite:///{database_path}",
        timeout_seconds=timeout_seconds,
    )
    adapter.initialize_schema()

    with adapter.engine.connect() as connection:
        busy_timeout_ms = connection.execute(text("PRAGMA busy_timeout")).scalar_one()

    assert busy_timeout_ms == int(timeout_seconds * 1000)
    adapter.engine.dispose()


def test_sqlite_adapter_skips_pragmas_for_non_sqlite_backend(tmp_path: Path) -> None:
    """Skip SQLite pragma initialization for non-SQLite backends."""
    adapter = SQLiteAdapter(database_url=f"sqlite:///{tmp_path / 'skip_pragmas.db'}")
    with patch("sqlalchemy.engine.url.URL.get_backend_name", return_value="postgresql"):
        adapter.initialize_schema()

    with adapter.engine.connect() as connection:
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()

    assert str(journal_mode).lower() != "wal"


def test_sqlite_schema_rejects_negative_scalar_metrics(sqlite_adapter: SQLiteAdapter) -> None:
    """Enforce non-negative scalar metric checks at schema level."""
    with sqlite_adapter.engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO submissions (
                    id,
                    project_id,
                    month,
                    created_at,
                    test_coverage,
                    overall_test_cases,
                    supported_releases_count,
                    raw_conversation
                ) VALUES (
                    :id,
                    :project_id,
                    :month,
                    :created_at,
                    :test_coverage,
                    :overall_test_cases,
                    :supported_releases_count,
                    :raw_conversation
                )
                """
            ),
            {
                "id": "negative-overall-test-cases",
                "project_id": "project-a",
                "month": "2026-01",
                "created_at": "2026-01-10T10:00:00+00:00",
                "test_coverage": "{}",
                "overall_test_cases": -1,
                "supported_releases_count": 1,
                "raw_conversation": None,
            },
        )


def test_sqlite_schema_rejects_invalid_month_format(sqlite_adapter: SQLiteAdapter) -> None:
    """Enforce month format and bounds checks at schema level."""
    with sqlite_adapter.engine.begin() as connection, pytest.raises(IntegrityError):
        connection.execute(
            text(
                """
                INSERT INTO submissions (
                    id,
                    project_id,
                    month,
                    created_at,
                    test_coverage,
                    overall_test_cases,
                    supported_releases_count,
                    raw_conversation
                ) VALUES (
                    :id,
                    :project_id,
                    :month,
                    :created_at,
                    :test_coverage,
                    :overall_test_cases,
                    :supported_releases_count,
                    :raw_conversation
                )
                """
            ),
            {
                "id": "invalid-month",
                "project_id": "project-a",
                "month": "2026-13",
                "created_at": "2026-01-10T10:00:00+00:00",
                "test_coverage": "{}",
                "overall_test_cases": 1,
                "supported_releases_count": 1,
                "raw_conversation": None,
            },
        )
