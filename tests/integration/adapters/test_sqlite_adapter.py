"""Integration tests for SQLite adapter."""

from __future__ import annotations

from pathlib import Path

from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter
from qa_chatbot.domain import DailyUpdate, Submission, TeamId, TimeWindow


def test_sqlite_adapter_persists_and_queries(tmp_path: Path) -> None:
    database_path = tmp_path / "qa_chatbot.db"
    adapter = SQLiteAdapter(database_url=f"sqlite:///{database_path}")
    adapter.initialize_schema()

    submission = Submission.create(
        team_id=TeamId("Team A"),
        month=TimeWindow.from_year_month(2026, 1),
        qa_metrics=None,
        project_status=None,
        daily_update=DailyUpdate(completed_tasks=("Done",)),
    )

    adapter.save_submission(submission)

    by_team = adapter.get_submissions_by_team(TeamId("Team A"), TimeWindow.from_year_month(2026, 1))
    by_month = adapter.get_submissions_by_month(TimeWindow.from_year_month(2026, 1))
    teams = adapter.get_all_teams()

    assert len(by_team) == 1
    assert by_team[0].team_id.value == "Team A"
    assert len(by_month) == 1
    assert teams == [TeamId("Team A")]