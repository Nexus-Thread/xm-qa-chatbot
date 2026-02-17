"""OpenAI SDK transport wrapper."""

from __future__ import annotations

from typing import Any


class OpenAIClient:
    """Thin transport wrapper around the OpenAI SDK client."""

    def __init__(self, sdk_client: Any) -> None:  # noqa: ANN401
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
