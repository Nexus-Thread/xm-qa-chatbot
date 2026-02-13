"""Unit tests for main application wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import qa_chatbot.main

if TYPE_CHECKING:
    import pytest


def test_main_wires_components(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure main constructs adapters and launches Gradio."""
    settings = MagicMock(
        log_level="INFO",
        database_url="sqlite:///./qa_chatbot.db",
        database_echo=False,
        dashboard_output_dir="./dashboard_html",
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
        openai_base_url="http://localhost",
        openai_api_key="test",
        openai_model="gpt-test",
        server_port=7860,
        share=False,
        input_max_chars=2000,
        rate_limit_requests=8,
        rate_limit_window_seconds=60,
    )
    monkeypatch.setattr(qa_chatbot.main, "EnvSettingsAdapter", lambda: MagicMock(load=lambda: settings))

    fake_storage = MagicMock()
    monkeypatch.setattr(qa_chatbot.main, "SQLiteAdapter", lambda **_: fake_storage)
    monkeypatch.setattr(qa_chatbot.main, "HtmlDashboardAdapter", lambda **_: MagicMock())
    monkeypatch.setattr(qa_chatbot.main, "OpenAIAdapter", lambda **_: MagicMock())
    metrics_adapter = MagicMock()
    monkeypatch.setattr(qa_chatbot.main, "InMemoryMetricsAdapter", lambda: metrics_adapter)
    monkeypatch.setattr(qa_chatbot.main, "ExtractStructuredDataUseCase", lambda **_: MagicMock())
    monkeypatch.setattr(qa_chatbot.main, "SubmitTeamDataUseCase", lambda **_: MagicMock())
    monkeypatch.setattr(qa_chatbot.main, "ConversationManager", lambda **_: MagicMock())
    gradio_adapter = MagicMock()
    monkeypatch.setattr(qa_chatbot.main, "GradioAdapter", lambda **_: gradio_adapter)

    qa_chatbot.main.main()

    fake_storage.initialize_schema.assert_called_once()
    gradio_adapter.launch.assert_called_once()
