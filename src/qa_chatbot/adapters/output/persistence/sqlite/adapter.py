"""SQLite adapter implementation."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from qa_chatbot.application.ports import StoragePort
from qa_chatbot.domain import Submission, TeamId, TimeWindow

from .mappers import model_to_submission, submission_to_model, time_window_from_iso
from .models import Base, SubmissionModel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine
    from sqlalchemy.sql import Select

    ScalarType = TypeVar("ScalarType")


class SQLiteAdapter(StoragePort):
    """SQLite implementation of the storage port."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        """Initialize the adapter with a database connection."""
        self._engine = create_engine(database_url, echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._logger = logging.getLogger(self.__class__.__name__)

    def initialize_schema(self) -> None:
        """Create database tables if needed."""
        Base.metadata.create_all(self._engine)

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission in SQLite."""
        with self._session_scope() as session:
            model = submission_to_model(submission)
            session.merge(model)

    def get_submissions_by_team(self, team_id: TeamId, month: TimeWindow) -> list[Submission]:
        """Return submissions for a team and month."""
        statement = select(SubmissionModel).where(
            SubmissionModel.team_id == team_id.value,
            SubmissionModel.month == month.to_iso_month(),
        )
        return self._execute_and_map(statement)

    def get_all_teams(self) -> list[TeamId]:
        """Return all team identifiers in sorted order."""
        statement = select(SubmissionModel.team_id).distinct().order_by(SubmissionModel.team_id)
        rows = self._execute_scalar(statement)
        return [TeamId(value) for value in rows]

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a given reporting month."""
        statement = select(SubmissionModel).where(SubmissionModel.month == month.to_iso_month())
        return self._execute_and_map(statement)

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return most recent reporting months in descending order."""
        statement = select(SubmissionModel.month).distinct().order_by(SubmissionModel.month.desc()).limit(limit)
        rows = self._execute_scalar(statement)
        return [time_window_from_iso(month) for month in rows]

    @property
    def engine(self) -> Engine:
        """Expose engine for advanced use cases."""
        return self._engine

    def _execute_and_map(self, statement: Select) -> list[Submission]:
        """Execute a query and map ORM rows to domain submissions."""
        models = self._execute_scalar(statement)
        return [model_to_submission(model) for model in models]

    def _execute_scalar(self, statement: Select[tuple[ScalarType]]) -> list[ScalarType]:
        """Execute a statement and return scalar rows."""
        with self._session_scope() as session:
            return list(session.execute(statement).scalars().all())

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        """Provide a transactional session scope."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            self._logger.exception("SQLite session error")
            session.rollback()
            raise
        finally:
            session.close()
