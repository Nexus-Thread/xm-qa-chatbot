"""Application-level settings DTO."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


@dataclass(frozen=True)
class AppSettings:
    """Application configuration values."""

    openai_base_url: str
    openai_api_key: str
    openai_model: str
    openai_max_retries: int
    openai_backoff_seconds: float
    database_url: str
    database_echo: bool
    dashboard_output_dir: Path
    jira_base_url: str
    jira_username: str
    jira_api_token: str
    server_port: int
    share: bool
    log_level: str
    input_max_chars: int
    rate_limit_requests: int
    rate_limit_window_seconds: int
