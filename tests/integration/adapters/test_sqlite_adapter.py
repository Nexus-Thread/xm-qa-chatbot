"""Integration tests for SQLite adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
    from qa_chatbot.domain import ProjectId, Submission, TimeWindow


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
