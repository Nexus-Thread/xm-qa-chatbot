"""SQLite adapter implementation."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from qa_chatbot.application.ports import StoragePort
from qa_chatbot.domain import ProjectId, Submission, TimeWindow

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
        """Persist a submission in SQLite, replacing any existing submission for the same project/month."""
        with self._session_scope() as session:
            # Delete existing submission for this project/month if present
            session.query(SubmissionModel).filter_by(
                project_id=submission.project_id.value,
                month=submission.month.to_iso_month(),
            ).delete()
            # Insert new submission
            model = submission_to_model(submission)
            session.add(model)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        """Return submissions for a project and month."""
        statement = select(SubmissionModel).where(
            SubmissionModel.project_id == project_id.value,
            SubmissionModel.month == month.to_iso_month(),
        )
        return self._execute_and_map(statement)

    def get_all_projects(self) -> list[ProjectId]:
        """Return all project identifiers in sorted order."""
        statement = select(SubmissionModel.project_id).distinct().order_by(SubmissionModel.project_id)
        rows: list[str] = self._execute_scalar(statement)
        return [ProjectId(value) for value in rows]

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return submissions for a given reporting month."""
        statement = select(SubmissionModel).where(SubmissionModel.month == month.to_iso_month())
        return self._execute_and_map(statement)

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return most recent reporting months in descending order."""
        statement = select(SubmissionModel.month).distinct().order_by(SubmissionModel.month.desc()).limit(limit)
        rows: list[str] = self._execute_scalar(statement)
        return [time_window_from_iso(month) for month in rows]

    def clear_all_submissions(self) -> None:
        """Delete all submissions from the database."""
        with self._session_scope() as session:
            session.query(SubmissionModel).delete()

    @property
    def engine(self) -> Engine:
        """Expose engine for advanced use cases."""
        return self._engine

    def _execute_and_map(self, statement: Select) -> list[Submission]:
        """Execute a query and map ORM rows to domain submissions."""
        models: list[SubmissionModel] = self._execute_scalar(statement)
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
