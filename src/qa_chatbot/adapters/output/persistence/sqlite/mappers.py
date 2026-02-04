"""Mappers between domain entities and ORM models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow

from .models import SubmissionModel


def submission_to_model(submission: Submission) -> SubmissionModel:
    """Map a domain submission to an ORM model."""
    return SubmissionModel(
        id=str(submission.id),
        project_id=submission.project_id.value,
        month=submission.month.to_iso_month(),
        created_at=submission.created_at,
        test_coverage=_test_coverage_to_dict(submission.test_coverage),
        overall_test_cases=submission.overall_test_cases,
        raw_conversation=submission.raw_conversation,
    )


def model_to_submission(model: SubmissionModel) -> Submission:
    """Map an ORM model to a domain submission."""
    created_at = model.created_at
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return Submission(
        id=UUID(model.id),
        project_id=ProjectId(model.project_id),
        month=time_window_from_iso(model.month),
        test_coverage=_test_coverage_from_dict(model.test_coverage),
        overall_test_cases=model.overall_test_cases,
        created_at=created_at,
        raw_conversation=model.raw_conversation,
    )


def _test_coverage_to_dict(metrics: TestCoverageMetrics | None) -> dict | None:
    if metrics is None:
        return None
    return {
        "manual_total": metrics.manual_total,
        "automated_total": metrics.automated_total,
        "manual_created_last_month": metrics.manual_created_last_month,
        "manual_updated_last_month": metrics.manual_updated_last_month,
        "automated_created_last_month": metrics.automated_created_last_month,
        "automated_updated_last_month": metrics.automated_updated_last_month,
        "percentage_automation": metrics.percentage_automation,
    }


def _test_coverage_from_dict(payload: dict | None) -> TestCoverageMetrics | None:
    if not payload:
        return None
    return TestCoverageMetrics(
        manual_total=payload["manual_total"],
        automated_total=payload["automated_total"],
        manual_created_last_month=payload["manual_created_last_month"],
        manual_updated_last_month=payload["manual_updated_last_month"],
        automated_created_last_month=payload["automated_created_last_month"],
        automated_updated_last_month=payload["automated_updated_last_month"],
        percentage_automation=payload["percentage_automation"],
    )


def time_window_from_iso(value: str) -> TimeWindow:
    """Parse YYYY-MM into a TimeWindow."""
    year_str, month_str = value.split("-")
    return TimeWindow.from_year_month(year=int(year_str), month=int(month_str))
