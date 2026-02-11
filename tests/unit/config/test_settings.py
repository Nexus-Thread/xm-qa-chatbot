"""Unit tests for environment settings adapter."""

from __future__ import annotations

import pytest

from qa_chatbot.adapters.input.env.adapter import EnvSettingsAdapter
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def test_settings_loads_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Load settings with defaults when env vars are absent."""
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "llama2")
    settings = EnvSettingsAdapter().load()

    assert settings.openai_base_url == "http://localhost:11434/v1"
    assert settings.openai_api_key == "test-key"
    assert settings.openai_model == "llama2"
    assert str(settings.reporting_config_path) == "config/reporting_config.yaml"


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


def test_settings_normalizes_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Normalize log level to uppercase."""
    monkeypatch.setenv("LOG_LEVEL", "warning")

    settings = EnvSettingsAdapter().load()

    assert settings.log_level == "WARNING"
