"""Daily update value object."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..exceptions import InvalidDailyUpdateError


@dataclass(frozen=True)
class DailyUpdate:
    """Daily status update for a reporting window."""

    completed_tasks: tuple[str, ...] = field(default_factory=tuple)
    planned_tasks: tuple[str, ...] = field(default_factory=tuple)
    capacity_hours: float | None = None
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.capacity_hours is not None and self.capacity_hours < 0:
            raise InvalidDailyUpdateError("Capacity hours must be non-negative")
        if any(not item.strip() for item in self.completed_tasks):
            raise InvalidDailyUpdateError("Completed tasks must not include empty items")
        if any(not item.strip() for item in self.planned_tasks):
            raise InvalidDailyUpdateError("Planned tasks must not include empty items")
        if any(not item.strip() for item in self.issues):
            raise InvalidDailyUpdateError("Issues must not include empty items")