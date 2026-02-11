"""Environment settings model and validation."""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from qa_chatbot.domain.exceptions import InvalidConfigurationError


class EnvSettings(BaseSettings):
    """Validated settings parsed from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    openai_base_url: str = Field(default="http://localhost:11434/v1", validation_alias="OPENAI_BASE_URL")
    openai_api_key: str = Field(default="ollama", validation_alias="OPENAI_API_KEY")
    openai_model: str = Field(default="llama2", validation_alias="OPENAI_MODEL")
    database_url: str = Field(default="sqlite:///./qa_chatbot.db", validation_alias="DATABASE_URL")
    database_echo: bool = Field(default=False, validation_alias="DATABASE_ECHO")
    dashboard_output_dir: Path = Field(default=Path("./dashboard_html"), validation_alias="DASHBOARD_OUTPUT_DIR")
    server_port: int = Field(default=7860, validation_alias="GRADIO_SERVER_PORT", ge=1, le=65535)
    share: bool = Field(default=False, validation_alias="GRADIO_SHARE")
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    input_max_chars: int = Field(default=2000, validation_alias="INPUT_MAX_CHARS", ge=1, le=10000)
    rate_limit_requests: int = Field(default=8, validation_alias="RATE_LIMIT_REQUESTS", ge=1, le=100)
    rate_limit_window_seconds: int = Field(default=60, validation_alias="RATE_LIMIT_WINDOW_SECONDS", ge=1, le=3600)

    def model_post_init(self, __context: object, /) -> None:
        """Validate and normalize values after parsing."""
        self._validate_non_empty("OPENAI_BASE_URL", self.openai_base_url)
        self._validate_non_empty("OPENAI_API_KEY", self.openai_api_key)
        self._validate_non_empty("OPENAI_MODEL", self.openai_model)
        self._validate_non_empty("DATABASE_URL", self.database_url)
        self.log_level = self._normalize_log_level(self.log_level)

    @staticmethod
    def _validate_non_empty(label: str, value: str) -> None:
        """Ensure required string values are not blank."""
        if not value.strip():
            message = f"{label} must be set"
            raise InvalidConfigurationError(message)

    @staticmethod
    def _normalize_log_level(value: str) -> str:
        """Normalize and validate log level."""
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR"}
        normalized = value.strip().upper()
        if normalized not in allowed:
            message = f"LOG_LEVEL must be one of {', '.join(sorted(allowed))}"
            raise InvalidConfigurationError(message)
        return normalized
