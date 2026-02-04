"""Application configuration loaded from environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Self

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_chatbot.domain.exceptions import InvalidConfigurationError


class AppSettings(BaseSettings):
    """Validated settings for the chatbot application."""

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
    log_format: str = Field("json", validation_alias="LOG_FORMAT")
    input_max_chars: int = Field(2000, validation_alias="INPUT_MAX_CHARS", ge=1, le=10000)
    rate_limit_requests: int = Field(8, validation_alias="RATE_LIMIT_REQUESTS", ge=1, le=100)
    rate_limit_window_seconds: int = Field(60, validation_alias="RATE_LIMIT_WINDOW_SECONDS", ge=1, le=3600)

    def model_post_init(self, __context: object, /) -> None:
        """Validate non-empty values after parsing."""
        self._validate_non_empty("OPENAI_BASE_URL", self.openai_base_url)
        self._validate_non_empty("OPENAI_API_KEY", self.openai_api_key)
        self._validate_non_empty("OPENAI_MODEL", self.openai_model)
        self._validate_non_empty("DATABASE_URL", self.database_url)
        self._validate_choice("LOG_LEVEL", self.log_level, {"DEBUG", "INFO", "WARNING", "ERROR"})
        self._validate_choice("LOG_FORMAT", self.log_format, {"json", "text"})

    @classmethod
    def load(cls) -> Self:
        """Load settings and surface configuration errors cleanly."""
        try:
            return cls()  # type: ignore[call-arg]
        except Exception as exc:  # pragma: no cover - handled as startup validation
            message = f"Invalid configuration: {exc}"
            raise InvalidConfigurationError(message) from exc

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
