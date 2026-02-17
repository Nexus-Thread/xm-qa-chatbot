"""Factory helpers for OpenAI transport clients."""

from __future__ import annotations

import httpx
from openai import OpenAI

from .constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_VERIFY_SSL
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
    verify_ssl: bool = DEFAULT_VERIFY_SSL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    http_client: httpx.Client | None = None,
) -> OpenAIClient:
    """Create an OpenAI-compatible client instance."""
    transport = http_client or build_http_client(verify_ssl=verify_ssl, timeout_seconds=timeout_seconds)
    sdk_client = OpenAI(base_url=base_url, api_key=api_key, http_client=transport)
    return OpenAIClient(sdk_client=sdk_client)
