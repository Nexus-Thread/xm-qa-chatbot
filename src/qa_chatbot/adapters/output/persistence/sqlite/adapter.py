"""SQLite adapter implementation."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .....application.ports import StoragePort
from .....domain import Submission, TeamId, TimeWindow
from .mappers import model_to_submission, submission_to_model
from .models import Base, SubmissionModel


class SQLiteAdapter(StoragePort):
    """SQLite implementation of the storage port."""

    def __init__(self, database_url: str, echo: bool = False) -> None:
        self._engine = create_engine(database_url, echo=echo, future=True)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)

    def initialize_schema(self) -> None:
        """Create database tables if needed."""

        Base.metadata.create_all(self._engine)

    def save_submission(self, submission: Submission) -> None:
        with self._session_scope() as session:
            model = submission_to_model(submission)
            session.merge(model)

    def get_submissions_by_team(self, team_id: TeamId, month: TimeWindow) -> list[Submission]:
        statement = select(SubmissionModel).where(
            SubmissionModel.team_id == team_id.value,
            SubmissionModel.month == month.to_iso_month(),
        )
        return self._execute_and_map(statement)

    def get_all_teams(self) -> list[TeamId]:
        statement = select(SubmissionModel.team_id).distinct().order_by(SubmissionModel.team_id)
        with self._session_scope() as session:
            rows = session.execute(statement).scalars().all()
        return [TeamId(value) for value in rows]

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        statement = select(SubmissionModel).where(SubmissionModel.month == month.to_iso_month())
        return self._execute_and_map(statement)

    @property
    def engine(self) -> Engine:
        """Expose engine for advanced use cases."""

        return self._engine

    def _execute_and_map(self, statement) -> list[Submission]:
        with self._session_scope() as session:
            models = session.execute(statement).scalars().all()
        return [model_to_submission(model) for model in models]

    @contextmanager
    def _session_scope(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()