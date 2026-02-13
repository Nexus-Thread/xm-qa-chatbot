"""Project entity."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class Project:
    """Represents a project within a business stream."""

    id: str
    name: str
    business_stream_id: str

    def __post_init__(self) -> None:
        """Validate project fields."""
        if not self.id.strip() or not self.name.strip() or not self.business_stream_id.strip():
            msg = "Project id, name, and business stream id are required"
            raise InvalidConfigurationError(msg)
