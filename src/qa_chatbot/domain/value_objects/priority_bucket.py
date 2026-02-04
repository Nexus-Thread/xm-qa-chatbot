"""Priority bucket value objects."""

from __future__ import annotations

from dataclasses import dataclass, field

from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class PriorityBucket:
    """Defines a priority bucket mapping."""

    name: str
    priorities: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate priority bucket mapping."""
        if not self.name.strip():
            msg = "Priority bucket name is required"
            raise InvalidConfigurationError(msg)
        if not self.priorities:
            msg = "Priority bucket must include at least one priority"
            raise InvalidConfigurationError(msg)
        if any(not priority.strip() for priority in self.priorities):
            msg = "Priority names must not be empty"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class PriorityMapping:
    """Defines the P1-P2 and P3-P4 buckets."""

    p1_p2: PriorityBucket
    p3_p4: PriorityBucket

    def __post_init__(self) -> None:
        """Ensure buckets do not overlap."""
        overlap = set(self.p1_p2.priorities) & set(self.p3_p4.priorities)
        if overlap:
            msg = f"Priority buckets overlap: {sorted(overlap)}"
            raise InvalidConfigurationError(msg)
