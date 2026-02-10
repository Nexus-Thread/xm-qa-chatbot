"""Pydantic schemas for LLM structured extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectIdSchema(BaseModel):
    """Schema for project identifier extraction."""

    project_id: str = Field(..., description="Project identifier or name")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")


class TimeWindowSchema(BaseModel):
    """Schema for reporting month extraction."""

    month: str = Field(..., description="Reporting month in YYYY-MM format")


class TestCoverageSchema(BaseModel):
    """Schema for test coverage extraction."""

    manual_total: int | None = None
    automated_total: int | None = None
    manual_created_last_month: int | None = None
    manual_updated_last_month: int | None = None
    automated_created_last_month: int | None = None
    automated_updated_last_month: int | None = None
