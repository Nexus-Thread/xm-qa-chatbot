"""Shared pytest fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterator

from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
from qa_chatbot.domain import DailyUpdate, Submission, TeamId, TimeWindow


@pytest.fixture
def team_id_a() -> TeamId:
    """Provide a default team identifier."""
    return TeamId("Team A")


@pytest.fixture
def team_id_b() -> TeamId:
    """Provide a secondary team identifier."""
    return TeamId("Team B")


@pytest.fixture
def time_window_jan() -> TimeWindow:
    """Provide a January 2026 reporting window."""
    return TimeWindow.from_year_month(2026, 1)


@pytest.fixture
def time_window_feb() -> TimeWindow:
    """Provide a February 2026 reporting window."""
    return TimeWindow.from_year_month(2026, 2)


@pytest.fixture
def daily_update_done() -> DailyUpdate:
    """Provide a minimal daily update payload."""
    return DailyUpdate(completed_tasks=("Done",))


@pytest.fixture
def submission_team_a_jan(
    team_id_a: TeamId,
    time_window_jan: TimeWindow,
    daily_update_done: DailyUpdate,
) -> Submission:
    """Provide a submission for Team A in January."""
    return Submission.create(
        team_id=team_id_a,
        month=time_window_jan,
        qa_metrics=None,
        project_status=None,
        daily_update=daily_update_done,
    )


@pytest.fixture
def sqlite_adapter(tmp_path: pytest.TempPathFactory) -> Iterator[SQLiteAdapter]:
    """Provide a SQLite adapter backed by a temporary database."""
    database_path = tmp_path / "qa_chatbot.db"
    adapter = SQLiteAdapter(database_url=f"sqlite:///{database_path}")
    adapter.initialize_schema()
    yield adapter
    adapter.engine.dispose()
