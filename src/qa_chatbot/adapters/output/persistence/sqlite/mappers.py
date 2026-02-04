"""Mappers between domain entities and ORM models."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, Submission, TeamId, TimeWindow

from .models import SubmissionModel


def submission_to_model(submission: Submission) -> SubmissionModel:
    """Map a domain submission to an ORM model."""
    return SubmissionModel(
        id=str(submission.id),
        team_id=submission.team_id.value,
        month=submission.month.to_iso_month(),
        created_at=submission.created_at,
        qa_metrics=_qa_metrics_to_dict(submission.qa_metrics),
        project_status=_project_status_to_dict(submission.project_status),
        daily_update=_daily_update_to_dict(submission.daily_update),
        raw_conversation=submission.raw_conversation,
    )


def model_to_submission(model: SubmissionModel) -> Submission:
    """Map an ORM model to a domain submission."""
    created_at = model.created_at
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)

    return Submission(
        id=UUID(model.id),
        team_id=TeamId(model.team_id),
        month=time_window_from_iso(model.month),
        qa_metrics=_qa_metrics_from_dict(model.qa_metrics),
        project_status=_project_status_from_dict(model.project_status),
        daily_update=_daily_update_from_dict(model.daily_update),
        created_at=created_at,
        raw_conversation=model.raw_conversation,
    )


def _qa_metrics_to_dict(metrics: QAMetrics | None) -> dict | None:
    if metrics is None:
        return None
    return {
        "tests_passed": metrics.tests_passed,
        "tests_failed": metrics.tests_failed,
        "test_coverage_percent": metrics.test_coverage_percent,
        "bug_count": metrics.bug_count,
        "critical_bugs": metrics.critical_bugs,
        "deployment_ready": metrics.deployment_ready,
    }


def _qa_metrics_from_dict(payload: dict | None) -> QAMetrics | None:
    if not payload:
        return None
    return QAMetrics(
        tests_passed=payload["tests_passed"],
        tests_failed=payload["tests_failed"],
        test_coverage_percent=payload.get("test_coverage_percent"),
        bug_count=payload.get("bug_count"),
        critical_bugs=payload.get("critical_bugs"),
        deployment_ready=payload.get("deployment_ready"),
    )


def _project_status_to_dict(status: ProjectStatus | None) -> dict | None:
    if status is None:
        return None
    return {
        "sprint_progress_percent": status.sprint_progress_percent,
        "blockers": list(status.blockers),
        "milestones_completed": list(status.milestones_completed),
        "risks": list(status.risks),
    }


def _project_status_from_dict(payload: dict | None) -> ProjectStatus | None:
    if not payload:
        return None
    return ProjectStatus(
        sprint_progress_percent=payload.get("sprint_progress_percent"),
        blockers=tuple(payload.get("blockers", [])),
        milestones_completed=tuple(payload.get("milestones_completed", [])),
        risks=tuple(payload.get("risks", [])),
    )


def _daily_update_to_dict(update: DailyUpdate | None) -> dict | None:
    if update is None:
        return None
    return {
        "completed_tasks": list(update.completed_tasks),
        "planned_tasks": list(update.planned_tasks),
        "capacity_hours": update.capacity_hours,
        "issues": list(update.issues),
    }


def _daily_update_from_dict(payload: dict | None) -> DailyUpdate | None:
    if not payload:
        return None
    return DailyUpdate(
        completed_tasks=tuple(payload.get("completed_tasks", [])),
        planned_tasks=tuple(payload.get("planned_tasks", [])),
        capacity_hours=payload.get("capacity_hours"),
        issues=tuple(payload.get("issues", [])),
    )


def time_window_from_iso(value: str) -> TimeWindow:
    """Parse YYYY-MM into a TimeWindow."""
    year_str, month_str = value.split("-")
    return TimeWindow.from_year_month(year=int(year_str), month=int(month_str))
