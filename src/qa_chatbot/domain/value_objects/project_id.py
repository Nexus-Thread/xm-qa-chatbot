"""Project identifier value object."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidProjectIdError


@dataclass(frozen=True)
class ProjectId:
    """Validated project identifier."""

    value: str

    def __post_init__(self) -> None:
        """Normalize and validate the project identifier."""
        normalized = self.value.strip()
        if not normalized:
            message = "Project ID must not be empty"
            raise InvalidProjectIdError(message)
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, value: str) -> ProjectId:
        """Create a ProjectId from raw input."""
        return cls(value=value)
