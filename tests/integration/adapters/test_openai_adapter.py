"""Integration tests for OpenAI adapter with Ollama."""

from __future__ import annotations

import os
from datetime import date

import pytest

from qa_chatbot.adapters.output.llm.openai import OpenAIAdapter, OpenAISettings
from qa_chatbot.domain import ExtractionConfidence, ProjectId, TimeWindow
from qa_chatbot.domain.registries import build_default_registry


@pytest.mark.skipif(
    os.getenv("OLLAMA_BASE_URL") is None,
    reason="OLLAMA_BASE_URL not configured",
)
def test_openai_adapter_with_ollama_extracts_project_id() -> None:
    """Extract a project identifier using Ollama."""
    settings = OpenAISettings(
        base_url=os.environ["OLLAMA_BASE_URL"],
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=os.getenv("OLLAMA_MODEL", "llama2"),
    )
    adapter = OpenAIAdapter(settings=settings)
    registry = build_default_registry()

    project_id, confidence = adapter.extract_project_id("We are the QA Automation project.", registry)

    assert isinstance(project_id, ProjectId)
    assert confidence in {
        ExtractionConfidence.from_raw("high"),
        ExtractionConfidence.from_raw("medium"),
        ExtractionConfidence.from_raw("low"),
    }


@pytest.mark.skipif(
    os.getenv("OLLAMA_BASE_URL") is None,
    reason="OLLAMA_BASE_URL not configured",
)
def test_openai_adapter_with_ollama_extracts_time_window() -> None:
    """Extract time window using Ollama."""
    settings = OpenAISettings(
        base_url=os.environ["OLLAMA_BASE_URL"],
        api_key=os.getenv("OLLAMA_API_KEY", "ollama"),
        model=os.getenv("OLLAMA_MODEL", "llama2"),
    )
    adapter = OpenAIAdapter(settings=settings)

    time_window = adapter.extract_time_window("Reporting for 2026-01", date(2026, 2, 1))

    assert time_window == TimeWindow.from_year_month(2026, 1)
