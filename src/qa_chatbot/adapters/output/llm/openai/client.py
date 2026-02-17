"""OpenAI client construction utilities."""

from __future__ import annotations

from typing import Protocol, cast

import httpx
from openai import OpenAI

DEFAULT_VERIFY_SSL = True
DEFAULT_TIMEOUT_SECONDS = 30.0


class OpenAIClientProtocol(Protocol):
    """Protocol for OpenAI chat completion transport."""

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> object:
        """Create a chat completion response in JSON mode."""


class ChatCompletionsProtocol(Protocol):
    """Protocol for completions API used by the wrapper."""

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str],
        temperature: float,
    ) -> object:
        """Create a completion using explicit JSON response format."""


class ChatNamespaceProtocol(Protocol):
    """Protocol for chat namespace used by the wrapper."""

    @property
    def completions(self) -> ChatCompletionsProtocol:
        """Return completions API."""


class OpenAISDKClientProtocol(Protocol):
    """Protocol for minimal SDK surface required by the wrapper."""

    @property
    def chat(self) -> ChatNamespaceProtocol:
        """Return chat namespace."""


class OpenAIClient:
    """Thin transport wrapper around the OpenAI SDK client."""

    def __init__(self, sdk_client: OpenAISDKClientProtocol) -> None:
        """Store the OpenAI SDK client."""
        self._sdk_client = sdk_client

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> object:
        """Create a JSON-formatted chat completion."""
        return self._sdk_client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=temperature,
        )


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
    sdk_client = cast("OpenAISDKClientProtocol", OpenAI(base_url=base_url, api_key=api_key, http_client=transport))
    return OpenAIClient(sdk_client=sdk_client)
