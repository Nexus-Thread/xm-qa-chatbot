"""Team identifier value object."""

from __future__ import annotations

from dataclasses import dataclass

from ..exceptions import InvalidTeamIdError


@dataclass(frozen=True)
class TeamId:
    """Validated team identifier."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip()
        if not normalized:
            raise InvalidTeamIdError("Team ID must not be empty")
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, value: str) -> "TeamId":
        """Create a TeamId from raw input."""

        return cls(value=value)