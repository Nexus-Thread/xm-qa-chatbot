"""Protocol for OpenAI transport interactions."""

from __future__ import annotations

from typing import Protocol


class OpenAIClientProtocol(Protocol):
    """Protocol for OpenAI chat completion transport."""

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> object:
        """Create a chat completion response in JSON mode."""
