"""Pydantic schemas for LLM structured extraction."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ProjectIdSchema(BaseModel):
    """Schema for project identifier extraction."""

    project_id: str = Field(..., description="Project identifier or name")
    confidence: str = Field(..., description="Confidence level: high, medium, or low")


class TimeWindowSchema(BaseModel):
    """Schema for reporting month extraction."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["iso_month", "current_month", "previous_month"]
    month: str | None = Field(
        default=None,
        description="Reporting month in YYYY-MM format when kind is iso_month",
        pattern=r"^\d{4}-\d{2}$",
    )

    @model_validator(mode="after")
    def validate_kind_month_combination(self) -> TimeWindowSchema:
        """Ensure month presence is consistent with extraction kind."""
        if self.kind == "iso_month" and self.month is None:
            msg = "month is required when kind is iso_month"
            raise ValueError(msg)
        if self.kind in {"current_month", "previous_month"} and self.month is not None:
            msg = "month must be null when kind is current_month or previous_month"
            raise ValueError(msg)
        return self


class TestCoverageSchema(BaseModel):
    """Schema for test coverage extraction."""

    manual_total: int | None = Field(default=None, ge=0)
    automated_total: int | None = Field(default=None, ge=0)
    manual_created_in_reporting_month: int | None = Field(default=None, ge=0)
    manual_updated_in_reporting_month: int | None = Field(default=None, ge=0)
    automated_created_in_reporting_month: int | None = Field(default=None, ge=0)
    automated_updated_in_reporting_month: int | None = Field(default=None, ge=0)
    supported_releases_count: int | None = Field(default=None, ge=0)
