"""Unit tests for main application wiring."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import qa_chatbot.main as main_module

if TYPE_CHECKING:
    import pytest


def test_main_wires_components(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure main constructs adapters and launches Gradio."""
    settings = MagicMock(
        log_level="INFO",
        log_format="json",
        database_url="sqlite:///./qa_chatbot.db",
        database_echo=False,
        dashboard_output_dir="./dashboard_html",
        openai_base_url="http://localhost",
        openai_api_key="test",
        openai_model="gpt-test",
        server_port=7860,
        share=False,
        input_max_chars=2000,
        rate_limit_requests=8,
        rate_limit_window_seconds=60,
    )
    monkeypatch.setattr(main_module.AppSettings, "load", lambda: settings)

    fake_storage = MagicMock()
    monkeypatch.setattr(main_module, "SQLiteAdapter", lambda **_: fake_storage)
    monkeypatch.setattr(main_module, "HtmlDashboardAdapter", lambda **_: MagicMock())
    monkeypatch.setattr(main_module, "OpenAIAdapter", lambda **_: MagicMock())
    metrics_adapter = MagicMock()
    monkeypatch.setattr(main_module, "InMemoryMetricsAdapter", lambda: metrics_adapter)
    monkeypatch.setattr(main_module, "ExtractStructuredDataUseCase", lambda **_: MagicMock())
    monkeypatch.setattr(main_module, "SubmitTeamDataUseCase", lambda **_: MagicMock())
    monkeypatch.setattr(main_module, "ConversationManager", lambda **_: MagicMock())
    gradio_adapter = MagicMock()
    monkeypatch.setattr(main_module, "GradioAdapter", lambda **_: gradio_adapter)

    main_module.main()

    fake_storage.initialize_schema.assert_called_once()
    gradio_adapter.launch.assert_called_once()
