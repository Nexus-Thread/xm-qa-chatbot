"""Environment configuration adapter."""

from __future__ import annotations

from pydantic import ValidationError

from qa_chatbot.application.dtos import AppSettings
from qa_chatbot.domain.exceptions import InvalidConfigurationError

from .settings import EnvSettings


class EnvSettingsAdapter:
    """Load application settings from environment variables."""

    def load(self) -> AppSettings:
        """Load and validate environment settings."""
        try:
            settings = EnvSettings()
        except ValidationError as exc:
            message = f"Invalid configuration: {exc}"
            raise InvalidConfigurationError(message) from exc
        return AppSettings(
            openai_base_url=settings.openai_base_url,
            openai_api_key=settings.openai_api_key,
            openai_model=settings.openai_model,
            openai_max_retries=settings.openai_max_retries,
            openai_backoff_seconds=settings.openai_backoff_seconds,
            openai_verify_ssl=settings.openai_verify_ssl,
            openai_timeout_seconds=settings.openai_timeout_seconds,
            database_url=settings.database_url,
            database_echo=settings.database_echo,
            database_timeout_seconds=settings.database_timeout_seconds,
            dashboard_output_dir=settings.dashboard_output_dir,
            dashboard_tailwind_script_src=settings.dashboard_tailwind_script_src,
            dashboard_plotly_script_src=settings.dashboard_plotly_script_src,
            jira_base_url=settings.jira_base_url,
            jira_username=settings.jira_username,
            jira_api_token=settings.jira_api_token,
            server_port=settings.server_port,
            share=settings.share,
            log_level=settings.log_level,
            log_format=settings.log_format,
            input_max_chars=settings.input_max_chars,
            rate_limit_requests=settings.rate_limit_requests,
            rate_limit_window_seconds=settings.rate_limit_window_seconds,
        )
