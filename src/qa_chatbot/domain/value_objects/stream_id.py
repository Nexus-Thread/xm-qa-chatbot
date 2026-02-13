"""Business stream identifier value object."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidStreamIdError


@dataclass(frozen=True)
class StreamId:
    """Validated business stream identifier."""

    value: str

    def __post_init__(self) -> None:
        """Normalize and validate the stream identifier."""
        normalized = self.value.strip()
        if not normalized:
            message = "Stream ID must not be empty"
            raise InvalidStreamIdError(message)
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, value: str) -> StreamId:
        """Create a StreamId from raw input."""
        return cls(value=value)
