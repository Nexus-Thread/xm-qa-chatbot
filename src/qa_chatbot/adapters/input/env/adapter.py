"""Environment configuration adapter."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_core import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_chatbot.application.dtos import AppSettings
from qa_chatbot.domain.exceptions import InvalidConfigurationError


class EnvSettingsAdapter:
    """Load application settings from environment variables."""

    def load(self) -> AppSettings:
        """Load and validate environment settings."""
        try:
            settings = _EnvSettings()
        except ValidationError as exc:
            message = f"Invalid configuration: {exc}"
            raise InvalidConfigurationError(message) from exc
        return AppSettings(
            openai_base_url=settings.openai_base_url,
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            database_url=settings.database_url,
            database_echo=settings.database_echo,
            dashboard_output_dir=settings.dashboard_output_dir,
            server_port=settings.server_port,
            share=settings.share,
            log_level=settings.log_level,
            input_max_chars=settings.input_max_chars,
            rate_limit_requests=settings.rate_limit_requests,
            rate_limit_window_seconds=settings.rate_limit_window_seconds,
        )


class _EnvSettings(BaseSettings):
    """Validated settings parsed from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_base_url: str = Field("http://localhost:11434/v1", validation_alias="OPENAI_BASE_URL")
    openai_api_key: str = Field("ollama", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field("llama2", validation_alias="OPENAI_MODEL")
    database_url: str = Field("sqlite:///./qa_chatbot.db", validation_alias="DATABASE_URL")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    dashboard_output_dir: Path = Field(Path("./dashboard_html"), validation_alias="DASHBOARD_OUTPUT_DIR")
    server_port: int = Field(7860, validation_alias="GRADIO_SERVER_PORT", ge=1, le=65535)
    share: bool = Field(default=False, validation_alias="GRADIO_SHARE")
    log_level: str = Field("INFO", validation_alias="LOG_LEVEL")
    input_max_chars: int = Field(2000, validation_alias="INPUT_MAX_CHARS", ge=1, le=10000)
    rate_limit_requests: int = Field(8, validation_alias="RATE_LIMIT_REQUESTS", ge=1, le=100)
    rate_limit_window_seconds: int = Field(60, validation_alias="RATE_LIMIT_WINDOW_SECONDS", ge=1, le=3600)

    def __init__(self, **data: Any) -> None:
        """Initialize settings with optional overrides."""
        super().__init__(**data)

    def model_post_init(self, __context: object, /) -> None:
        """Validate non-empty values after parsing."""
        self._validate_non_empty("OPENAI_BASE_URL", self.openai_base_url)
        self._validate_non_empty("OPENAI_API_KEY", self.openai_api_key)
        self._validate_non_empty("OPENAI_MODEL", self.openai_model)
        self._validate_non_empty("DATABASE_URL", self.database_url)
        self._validate_choice("LOG_LEVEL", self.log_level, {"DEBUG", "INFO", "WARNING", "ERROR"})

    @staticmethod
    def _validate_non_empty(label: str, value: str) -> None:
        """Ensure required configuration values are not blank."""
        if not value.strip():
            message = f"{label} must be set"
            raise InvalidConfigurationError(message)

    @staticmethod
    def _validate_choice(label: str, value: str, allowed: set[str]) -> None:
        """Ensure a configuration value is within allowed choices."""
        normalized = value.strip().upper() if label == "LOG_LEVEL" else value.strip().lower()
        normalized_allowed = {option.upper() if label == "LOG_LEVEL" else option.lower() for option in allowed}
        if normalized not in normalized_allowed:
            message = f"{label} must be one of {', '.join(sorted(allowed))}"
            raise InvalidConfigurationError(message)
