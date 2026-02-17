"""Prompt templates for OpenAI extraction."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain.registries import StreamProjectRegistry

SYSTEM_PROMPT = "You are a careful data extraction assistant for quality assurance projects. Return structured JSON that matches the provided schema, without commentary."


def build_project_id_prompt(registry: StreamProjectRegistry) -> str:
    """Build project identification prompt with valid project list."""
    projects = registry.active_projects()
    project_list = "\n".join([f"- {p.id}: {p.name}" for p in sorted(projects, key=lambda x: x.id)])

    return f"""Extract the project name from the conversation and match it to one of these valid projects:

{project_list}

Match the user's input to the most appropriate project. Handle typos, partial names, and abbreviations.

Return JSON with:
- project_id: the matched project ID (e.g., "bridge", "jthales")
- confidence: "high" (exact/clear match), "medium" (likely match with minor uncertainty), or "low" (very uncertain or no clear match)

If the user's input doesn't clearly match any project, return the closest match with "low" confidence."""


TIME_WINDOW_PROMPT = "Extract the reporting month from the conversation. Return it in YYYY-MM format (e.g., 2026-01)."

TEST_COVERAGE_PROMPT = (
    "Extract test coverage metrics from the conversation. "
    "Return JSON with these exact fields: "
    "manual_total, automated_total, manual_created_in_reporting_month, manual_updated_in_reporting_month, "
    "automated_created_in_reporting_month, automated_updated_in_reporting_month, supported_releases_count. "
    "Each field is an integer or null. Use null for any field not mentioned in the conversation."
)
