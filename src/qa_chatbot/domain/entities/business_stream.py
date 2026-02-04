"""Business stream entity."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class BusinessStream:
    """Represents a business stream in the portfolio."""

    id: str
    name: str
    order: int

    def __post_init__(self) -> None:
        """Validate business stream fields."""
        if not self.id.strip() or not self.name.strip():
            msg = "Business stream id and name must be provided"
            raise InvalidConfigurationError(msg)
        if self.order < 0:
            msg = "Business stream order must be non-negative"
            raise InvalidConfigurationError(msg)
