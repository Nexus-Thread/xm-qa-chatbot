"""Pydantic schemas for LLM structured extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ProjectIdSchema(BaseModel):
    """Schema for project identifier extraction."""

    project_id: str = Field(..., description="Project identifier or name")


class TimeWindowSchema(BaseModel):
    """Schema for reporting month extraction."""

    month: str = Field(..., description="Reporting month in YYYY-MM format")


class TestCoverageSchema(BaseModel):
    """Schema for test coverage extraction."""

    manual_total: int
    automated_total: int
    manual_created_last_month: int
    manual_updated_last_month: int
    automated_created_last_month: int
    automated_updated_last_month: int
