"""Project entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import StreamId


@dataclass(frozen=True)
class Project:
    """Represents a project within a business stream."""

    id: str
    name: str
    business_stream_id: StreamId

    def __post_init__(self) -> None:
        """Validate project fields."""
        if not self.id.strip() or not self.name.strip():
            msg = "Project id and name are required"
            raise InvalidConfigurationError(msg)
