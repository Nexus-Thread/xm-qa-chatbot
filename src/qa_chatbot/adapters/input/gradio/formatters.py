"""Formatting helpers for Gradio chatbot responses."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow

if TYPE_CHECKING:
    from datetime import date


def welcome_message(today: date) -> str:
    """Return the opening welcome message."""
    default_window = TimeWindow.default_for(today)
    return (
        "Hi! I can help collect your monthly QA update, including project notes and metrics. "
        f"This will default to {default_window.to_iso_month()} unless you specify another month. "
        "Which stream/project are you reporting for?"
    )


def prompt_for_project() -> str:
    """Return the prompt for project identification."""
    return "Which stream/project are you reporting for?"


def prompt_for_time_window(default_window: TimeWindow) -> str:
    """Return the prompt for reporting month selection."""
    return f"Which reporting month should be used? (Default: {default_window.to_iso_month()})"


def prompt_for_test_coverage() -> str:
    """Return the prompt for test coverage collection."""
    return (
        "Share any test coverage details you have (manual/automated totals or created/updated counts). "
        "It's OK to provide only part of the data."
    )


def prompt_for_confirmation(summary: str) -> str:
    """Return the confirmation prompt."""
    return f"Here is what I captured:\n\n{summary}\n\nReply with 'yes' to save or tell me what to change."


def format_extraction_summary(result: ExtractionResult) -> str:
    """Format an extraction result into a readable summary."""
    lines = [f"Project: {result.project_id.value}", f"Month: {result.time_window.to_iso_month()}"]
    if result.test_coverage:
        lines.append(_format_test_coverage(result.test_coverage))
    return "\n".join(lines)


def format_submission_summary(
    project_id: ProjectId,
    time_window: TimeWindow,
    test_coverage: TestCoverageMetrics | None,
    overall_test_cases: int | None,
) -> str:
    """Format the current conversation data into a summary."""
    summary = ExtractionResult(
        project_id=project_id,
        time_window=time_window,
        test_coverage=test_coverage,
        overall_test_cases=overall_test_cases,
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


def _format_test_coverage(metrics: TestCoverageMetrics) -> str:
    """Format test coverage metrics into a summary block."""
    parts = [
        "Test Coverage:",
        f"- Manual total: {metrics.manual_total}",
        f"- Automated total: {metrics.automated_total}",
        f"- Manual created last month: {metrics.manual_created_last_month}",
        f"- Manual updated last month: {metrics.manual_updated_last_month}",
        f"- Automated created last month: {metrics.automated_created_last_month}",
        f"- Automated updated last month: {metrics.automated_updated_last_month}",
    ]
    return "\n".join(parts)
