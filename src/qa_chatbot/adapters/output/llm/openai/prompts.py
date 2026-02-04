"""Prompt templates for OpenAI extraction."""

SYSTEM_PROMPT = (
    "You are a careful data extraction assistant for software development teams. "
    "Return structured JSON that matches the provided schema, without commentary."
)

PROJECT_ID_PROMPT = (
    "Extract the project identifier or project name from the conversation. Use the exact project name if provided."
)
TIME_WINDOW_PROMPT = "Extract the reporting month from the conversation. Return it in YYYY-MM format (e.g., 2026-01)."
TEST_COVERAGE_PROMPT = (
    "Extract test coverage metrics from the conversation. "
    "Include manual/automated totals and created/updated counts for last month."
)
OVERALL_TEST_CASES_PROMPT = (
    "Extract the overall number of test cases across all projects (portfolio total) if provided."
)
