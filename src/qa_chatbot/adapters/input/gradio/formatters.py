"""Formatting helpers for Gradio chatbot responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow

if TYPE_CHECKING:
    from datetime import date


def welcome_message(today: date) -> str:
    """Return the opening welcome message."""
    default_window = TimeWindow.default_for(today)
    return (
        "Hi! I can help collect QA metrics and project updates. "
        f"This will default to {default_window.to_iso_month()} unless you specify another month. "
        "Which team are you from?"
    )


def prompt_for_team_id() -> str:
    """Return the prompt for team identification."""
    return "Which team are you reporting for?"


def prompt_for_time_window(default_window: TimeWindow) -> str:
    """Return the prompt for reporting month selection."""
    return f"Which reporting month should I use? (Default: {default_window.to_iso_month()})"


def prompt_for_qa_metrics() -> str:
    """Return the prompt for QA metrics collection."""
    return (
        "Tell me about your QA metrics. Include tests passed/failed, coverage %, "
        "bug counts, and deployment readiness if you have them."
    )


def prompt_for_project_status() -> str:
    """Return the prompt for project status collection."""
    return "Share your project status. Include sprint progress %, blockers, milestones completed, and any risks."


def prompt_for_daily_update() -> str:
    """Return the prompt for daily update collection."""
    return "What are your daily updates? Include completed tasks, planned work, capacity hours, and issues."


def prompt_for_confirmation(summary: str) -> str:
    """Return the confirmation prompt."""
    return f"Here is what I captured:\n\n{summary}\n\nReply with 'yes' to save or tell me what to change."


def format_extraction_summary(result: ExtractionResult) -> str:
    """Format an extraction result into a readable summary."""
    lines = [f"Team: {result.team_id.value}", f"Month: {result.time_window.to_iso_month()}"]
    if result.qa_metrics:
        lines.append(_format_qa_metrics(result.qa_metrics))
    if result.project_status:
        lines.append(_format_project_status(result.project_status))
    if result.daily_update:
        lines.append(_format_daily_update(result.daily_update))
    return "\n".join(lines)


def format_submission_summary(
    team_id: TeamId,
    time_window: TimeWindow,
    qa_metrics: QAMetrics | None,
    project_status: ProjectStatus | None,
    daily_update: DailyUpdate | None,
) -> str:
    """Format the current conversation data into a summary."""
    summary = ExtractionResult(
        team_id=team_id,
        time_window=time_window,
        qa_metrics=qa_metrics,
        project_status=project_status,
        daily_update=daily_update,
    )
    return format_extraction_summary(summary)


def format_error_message(message: str) -> str:
    """Format an error message for the chat UI."""
    return f"I ran into an issue: {message}"


def format_skip_confirmation(section_label: str) -> str:
    """Format a confirmation prompt when a section is skipped."""
    return f"Okay, we can skip {section_label}. Reply with 'yes' to confirm, or send details if you want to include it."


def format_saved_message() -> str:
    """Return the success message after saving."""
    return "Thanks! Your update has been saved."


def format_edit_prompt(section_label: str) -> str:
    """Return a prompt asking the user to edit a section."""
    return f"Got it. Please share the corrected details for {section_label}."


def _format_qa_metrics(qa_metrics: QAMetrics) -> str:
    """Format QA metrics into a summary block."""
    parts = [
        "QA Metrics:",
        f"- Tests passed: {qa_metrics.tests_passed}",
        f"- Tests failed: {qa_metrics.tests_failed}",
    ]
    if qa_metrics.test_coverage_percent is not None:
        parts.append(f"- Coverage: {qa_metrics.test_coverage_percent}%")
    if qa_metrics.bug_count is not None:
        parts.append(f"- Bugs: {qa_metrics.bug_count}")
    if qa_metrics.critical_bugs is not None:
        parts.append(f"- Critical bugs: {qa_metrics.critical_bugs}")
    if qa_metrics.deployment_ready is not None:
        parts.append(f"- Deployment ready: {qa_metrics.deployment_ready}")
    return "\n".join(parts)


def _format_project_status(project_status: ProjectStatus) -> str:
    """Format project status into a summary block."""
    parts = ["Project Status:"]
    if project_status.sprint_progress_percent is not None:
        parts.append(f"- Sprint progress: {project_status.sprint_progress_percent}%")
    if project_status.blockers:
        parts.append(f"- Blockers: {', '.join(project_status.blockers)}")
    if project_status.milestones_completed:
        parts.append(f"- Milestones completed: {', '.join(project_status.milestones_completed)}")
    if project_status.risks:
        parts.append(f"- Risks: {', '.join(project_status.risks)}")
    return "\n".join(parts)


def _format_daily_update(daily_update: DailyUpdate) -> str:
    """Format daily update into a summary block."""
    parts = ["Daily Update:"]
    if daily_update.completed_tasks:
        parts.append(f"- Completed: {', '.join(daily_update.completed_tasks)}")
    if daily_update.planned_tasks:
        parts.append(f"- Planned: {', '.join(daily_update.planned_tasks)}")
    if daily_update.capacity_hours is not None:
        parts.append(f"- Capacity hours: {daily_update.capacity_hours}")
    if daily_update.issues:
        parts.append(f"- Issues: {', '.join(daily_update.issues)}")
    return "\n".join(parts)
