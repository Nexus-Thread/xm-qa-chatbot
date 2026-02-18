"""Unit tests for Gradio response formatting helpers."""

from qa_chatbot.adapters.input.gradio import formatters
from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow


def test_format_extraction_summary_includes_coverage_when_available() -> None:
    """Include project, month, releases, and coverage details in extraction summary output."""
    result = ExtractionResult(
        project_id=ProjectId("project-a"),
        time_window=TimeWindow.from_year_month(2026, 1),
        metrics=SubmissionMetrics(
            test_coverage=TestCoverageMetrics(
                manual_total=10,
                automated_total=5,
                manual_created_in_reporting_month=1,
                manual_updated_in_reporting_month=1,
                automated_created_in_reporting_month=1,
                automated_updated_in_reporting_month=1,
            ),
            overall_test_cases=None,
            supported_releases_count=2,
        ),
    )

    summary = formatters.format_extraction_summary(result)

    assert "Project: project-a" in summary
    assert "Month: 2026-01" in summary
    assert "Supported releases count: 2" in summary
    assert "Test Coverage:" in summary
    assert "- Manual total: 10" in summary


def test_format_edit_prompt_mentions_requested_section() -> None:
    """Echo the requested section label in edit prompts."""
    prompt = formatters.format_edit_prompt("test coverage")

    assert "corrected details" in prompt
    assert "test coverage" in prompt
