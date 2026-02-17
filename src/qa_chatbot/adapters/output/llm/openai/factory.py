"""Factory helpers for OpenAI transport clients."""

from __future__ import annotations

import httpx
from openai import OpenAI

from .constants import DEFAULT_BACKOFF_SECONDS, DEFAULT_MAX_RETRIES, DEFAULT_TIMEOUT_SECONDS, DEFAULT_VERIFY_SSL
from .transport import OpenAIClient


def build_http_client(
    *,
    verify_ssl: bool = DEFAULT_VERIFY_SSL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> httpx.Client:
    """Create an httpx client used by OpenAI SDK transport."""
    timeout = httpx.Timeout(timeout_seconds)
    return httpx.Client(verify=verify_ssl, timeout=timeout)


def build_client(
    base_url: str,
    api_key: str,
    *,
    transport: httpx.Client | None = None,
    max_retries: int = DEFAULT_MAX_RETRIES,
    backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
) -> OpenAIClient:
    """Create an OpenAI-compatible client instance."""
    http_client = transport or build_http_client(
        verify_ssl=DEFAULT_VERIFY_SSL,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
    )
    sdk_client = OpenAI(base_url=base_url, api_key=api_key, http_client=http_client)
    return OpenAIClient(
        sdk_client=sdk_client,
        max_retries=max_retries,
        backoff_seconds=backoff_seconds,
    )
