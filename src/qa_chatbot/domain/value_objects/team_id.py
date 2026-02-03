"""Team identifier value object."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidTeamIdError


@dataclass(frozen=True)
class TeamId:
    """Validated team identifier."""

    value: str

    def __post_init__(self) -> None:
        """Normalize and validate the team identifier."""
        normalized = self.value.strip()
        if not normalized:
            message = "Team ID must not be empty"
            raise InvalidTeamIdError(message)
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, value: str) -> TeamId:
        """Create a TeamId from raw input."""
        return cls(value=value)
