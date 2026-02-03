"""Prompt templates for OpenAI extraction."""

SYSTEM_PROMPT = (
    "You are a careful data extraction assistant for software development teams. "
    "Return structured JSON that matches the provided schema, without commentary."
)

TEAM_ID_PROMPT = (
    "Extract the team identifier or team name from the conversation. Use the most specific team name available."
)
TIME_WINDOW_PROMPT = "Extract the reporting month from the conversation. Return it in YYYY-MM format (e.g., 2026-01)."
QA_METRICS_PROMPT = (
    "Extract QA metrics from the conversation. "
    "Include test counts, coverage percent, bug counts, and deployment readiness if mentioned."
)
PROJECT_STATUS_PROMPT = (
    "Extract project status updates from the conversation. "
    "Include sprint progress percent, blockers, milestones completed, and risks if mentioned."
)
DAILY_UPDATE_PROMPT = (
    "Extract daily update details from the conversation. "
    "Include completed tasks, planned tasks, capacity hours, and issues if mentioned."
)
