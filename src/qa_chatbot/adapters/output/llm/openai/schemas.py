"""Pydantic schemas for LLM structured extraction."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TeamIdSchema(BaseModel):
    """Schema for team identifier extraction."""

    team_id: str = Field(..., description="Team identifier or name")


class TimeWindowSchema(BaseModel):
    """Schema for reporting month extraction."""

    month: str = Field(..., description="Reporting month in YYYY-MM format")


class QAMetricsSchema(BaseModel):
    """Schema for QA metric extraction."""

    tests_passed: int
    tests_failed: int
    test_coverage_percent: float | None = None
    bug_count: int | None = None
    critical_bugs: int | None = None
    deployment_ready: bool | None = None


class ProjectStatusSchema(BaseModel):
    """Schema for project status extraction."""

    sprint_progress_percent: float | None = None
    blockers: list[str] = Field(default_factory=list)
    milestones_completed: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)


class DailyUpdateSchema(BaseModel):
    """Schema for daily update extraction."""

    completed_tasks: list[str] = Field(default_factory=list)
    planned_tasks: list[str] = Field(default_factory=list)
    capacity_hours: float | None = None
    issues: list[str] = Field(default_factory=list)
