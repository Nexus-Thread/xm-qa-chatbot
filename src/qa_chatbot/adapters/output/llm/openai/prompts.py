"""Prompt templates for OpenAI extraction."""

SYSTEM_PROMPT = (
    "You are a helpful data collection assistant for software development teams. "
    "Extract structured information about QA metrics, project status, and daily updates."
)

TEAM_ID_PROMPT = "Extract the team identifier from the conversation."
TIME_WINDOW_PROMPT = "Extract the reporting month from the conversation."
QA_METRICS_PROMPT = "Extract QA metrics from the conversation."
PROJECT_STATUS_PROMPT = "Extract project status from the conversation."
DAILY_UPDATE_PROMPT = "Extract daily update information from the conversation."
