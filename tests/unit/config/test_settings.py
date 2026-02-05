"""Unit tests for environment settings adapter."""

from __future__ import annotations

import pytest

from qa_chatbot.adapters.input.env.adapter import EnvSettingsAdapter
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def test_settings_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load settings with defaults when env vars are absent."""
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    settings = EnvSettingsAdapter().load()

    assert settings.openai_base_url
    assert settings.openai_api_key
    assert settings.openai_model


def test_settings_rejects_empty_values(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise when required values are blank."""
    monkeypatch.setenv("OPENAI_BASE_URL", " ")

    with pytest.raises(InvalidConfigurationError):
        EnvSettingsAdapter().load()


def test_settings_rejects_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Raise when log level is not allowed."""
    monkeypatch.setenv("LOG_LEVEL", "verbose")

    with pytest.raises(InvalidConfigurationError):
        EnvSettingsAdapter().load()
