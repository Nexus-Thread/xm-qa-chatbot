"""SQLite adapter implementation."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import create_engine, delete, select, text
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from qa_chatbot.application.ports import StoragePort
from qa_chatbot.domain import ProjectId, StorageOperationError, Submission, TimeWindow

from .mappers import model_to_submission, submission_to_model, time_window_from_iso
from .models import Base, SubmissionModel

if TYPE_CHECKING:
    from collections.abc import Iterator

    from sqlalchemy.engine import Engine
    from sqlalchemy.sql import Select

    ScalarType = TypeVar("ScalarType")

LOGGER = logging.getLogger(__name__)

MILLISECONDS_PER_SECOND = 1000
DEFAULT_TIMEOUT_SECONDS = 5.0


class SQLiteAdapter(StoragePort):
    """SQLite implementation of the storage port."""

    def __init__(
        self,
        database_url: str,
        *,
        echo: bool = False,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the adapter with a database connection."""
        connect_args: dict[str, float] = {}
        if database_url.startswith("sqlite"):
            connect_args["timeout"] = timeout_seconds
        self._engine = create_engine(
            database_url,
            echo=echo,
            future=True,
            connect_args=connect_args,
        )
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        self._timeout_seconds = timeout_seconds

    def initialize_schema(self) -> None:
        """Create database tables if needed."""
        Base.metadata.create_all(self._engine)
        self._initialize_sqlite_pragmas()

    def save_submission(self, submission: Submission) -> None:
        """Persist a submission in SQLite, replacing any existing submission for the same project/month."""
        model = submission_to_model(submission)
        values = {
            "id": model.id,
            "project_id": model.project_id,
            "month": model.month,
            "created_at": model.created_at,
            "test_coverage": model.test_coverage,
            "overall_test_cases": model.overall_test_cases,
            "supported_releases_count": model.supported_releases_count,
            "raw_conversation": model.raw_conversation,
        }
        statement = sqlite_insert(SubmissionModel).values(**values)
        upsert_statement = statement.on_conflict_do_update(
            index_elements=["project_id", "month"],
            set_=values,
        )
        with self._write_session_scope() as session:
            session.execute(upsert_statement)

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
        with self._write_session_scope() as session:
            session.execute(delete(SubmissionModel))

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
        with self._read_session_scope() as session:
            return list(session.execute(statement).scalars().all())

    @contextmanager
    def _write_session_scope(self) -> Iterator[Session]:
        """Provide a transactional session scope for write operations."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as err:
            session.rollback()
            LOGGER.exception(
                "SQLite write operation failed",
                extra={
                    "component": self.__class__.__name__,
                    "operation": "write",
                    "error_type": type(err).__name__,
                },
            )
            msg = "SQLite write operation failed"
            raise StorageOperationError(msg) from err
        finally:
            session.close()

    @contextmanager
    def _read_session_scope(self) -> Iterator[Session]:
        """Provide a session scope for read operations."""
        session = self._session_factory()
        try:
            yield session
        except SQLAlchemyError as err:
            LOGGER.exception(
                "SQLite read operation failed",
                extra={
                    "component": self.__class__.__name__,
                    "operation": "read",
                    "error_type": type(err).__name__,
                },
            )
            msg = "SQLite read operation failed"
            raise StorageOperationError(msg) from err
        finally:
            session.close()

    def _initialize_sqlite_pragmas(self) -> None:
        """Initialize SQLite runtime pragmas for reliability."""
        if self._engine.url.get_backend_name() != "sqlite":
            return

        busy_timeout_ms = int(self._timeout_seconds * MILLISECONDS_PER_SECOND)
        with self._engine.begin() as connection:
            connection.execute(text("PRAGMA journal_mode=WAL"))
            connection.exec_driver_sql(f"PRAGMA busy_timeout={busy_timeout_ms}")
