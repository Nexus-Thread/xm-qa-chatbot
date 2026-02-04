"""Shared pytest fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow


@pytest.fixture
def project_id_a() -> ProjectId:
    """Provide a default project identifier."""
    return ProjectId("project-a")


@pytest.fixture
def project_id_b() -> ProjectId:
    """Provide a secondary project identifier."""
    return ProjectId("project-b")


@pytest.fixture
def time_window_jan() -> TimeWindow:
    """Provide a January 2026 reporting window."""
    return TimeWindow.from_year_month(2026, 1)


@pytest.fixture
def time_window_feb() -> TimeWindow:
    """Provide a February 2026 reporting window."""
    return TimeWindow.from_year_month(2026, 2)


@pytest.fixture
def test_coverage_done() -> TestCoverageMetrics:
    """Provide a minimal test coverage payload."""
    return TestCoverageMetrics(
        manual_total=10,
        automated_total=5,
        manual_created_last_month=1,
        manual_updated_last_month=1,
        automated_created_last_month=1,
        automated_updated_last_month=1,
        percentage_automation=33.33,
    )


@pytest.fixture
def submission_project_a_jan(
    project_id_a: ProjectId,
    time_window_jan: TimeWindow,
    test_coverage_done: TestCoverageMetrics,
) -> Submission:
    """Provide a submission for Project A in January."""
    return Submission.create(
        project_id=project_id_a,
        month=time_window_jan,
        test_coverage=test_coverage_done,
        overall_test_cases=25,
    )


@pytest.fixture
def sqlite_adapter(tmp_path: Path) -> Iterator[SQLiteAdapter]:
    """Provide a SQLite adapter backed by a temporary database."""
    database_path = tmp_path / "qa_chatbot.db"
    adapter = SQLiteAdapter(database_url=f"sqlite:///{database_path}")
    adapter.initialize_schema()
    yield adapter
    adapter.engine.dispose()
