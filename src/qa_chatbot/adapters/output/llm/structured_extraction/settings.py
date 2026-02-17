"""Configuration and usage models for structured extraction."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.adapters.output.llm.openai import (
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_VERIFY_SSL,
)


@dataclass(frozen=True)
class TokenUsage:
    """Token usage details for a single extraction."""

    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


@dataclass(frozen=True)
class OpenAISettings:
    """Configuration settings for the OpenAI adapter."""

    base_url: str
    api_key: str
    model: str
    max_retries: int = DEFAULT_MAX_RETRIES
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS
    verify_ssl: bool = DEFAULT_VERIFY_SSL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
