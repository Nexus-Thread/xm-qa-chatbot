"""SQLAlchemy models for SQLite persistence."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import JSON, CheckConstraint, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class SubmissionModel(Base):
    """Submission table schema."""

    __tablename__ = "submissions"
    __table_args__ = (
        UniqueConstraint("project_id", "month", name="uq_project_month"),
        CheckConstraint(
            "overall_test_cases IS NULL OR overall_test_cases >= 0",
            name="ck_submissions_overall_test_cases_non_negative",
        ),
        CheckConstraint(
            "supported_releases_count IS NULL OR supported_releases_count >= 0",
            name="ck_submissions_supported_releases_non_negative",
        ),
        CheckConstraint(
            "length(month) = 7 AND substr(month, 5, 1) = '-' "
            "AND CAST(substr(month, 1, 4) AS INTEGER) BETWEEN 2000 AND 2100 "
            "AND CAST(substr(month, 6, 2) AS INTEGER) BETWEEN 1 AND 12",
            name="ck_submissions_month_iso",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    project_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    month: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(tz=UTC),
    )
    test_coverage: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    overall_test_cases: Mapped[int | None] = mapped_column(Integer, nullable=True)
    supported_releases_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_conversation: Mapped[str | None] = mapped_column(String, nullable=True)
