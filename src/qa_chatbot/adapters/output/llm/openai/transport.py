"""OpenAI SDK transport wrapper."""

from __future__ import annotations

from typing import Protocol, cast


class _ChatCompletionsProtocol(Protocol):
    """Private protocol for the SDK completions namespace."""

    def create(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        response_format: dict[str, str],
        temperature: float,
    ) -> object:
        """Create a completion response from the SDK."""


class _ChatNamespaceProtocol(Protocol):
    """Private protocol for the SDK chat namespace."""

    @property
    def completions(self) -> _ChatCompletionsProtocol:
        """Return the completions API namespace."""


class _OpenAISDKClientProtocol(Protocol):
    """Private protocol for minimal OpenAI SDK client shape."""

    @property
    def chat(self) -> _ChatNamespaceProtocol:
        """Return the chat API namespace."""


class OpenAIClient:
    """Thin transport wrapper around the OpenAI SDK client."""

    def __init__(self, sdk_client: object) -> None:
        """Store the OpenAI SDK client."""
        self._sdk_client = cast("_OpenAISDKClientProtocol", sdk_client)

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
