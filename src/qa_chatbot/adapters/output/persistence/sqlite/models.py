"""SQLAlchemy models for SQLite persistence."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, DateTime, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class SubmissionModel(Base):
    """Submission table schema."""

    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("team_id", "month", name="uq_team_month"),)

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    team_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    month: Mapped[str] = mapped_column(String, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    qa_metrics: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    project_status: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    daily_update: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_conversation: Mapped[str | None] = mapped_column(String, nullable=True)