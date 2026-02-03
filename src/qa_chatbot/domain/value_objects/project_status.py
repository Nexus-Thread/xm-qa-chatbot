"""Project status value object."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..exceptions import InvalidProjectStatusError


@dataclass(frozen=True)
class ProjectStatus:
    """Project tracking information for a reporting window."""

    sprint_progress_percent: float | None = None
    blockers: tuple[str, ...] = field(default_factory=tuple)
    milestones_completed: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.sprint_progress_percent is not None and not 0 <= self.sprint_progress_percent <= 100:
            raise InvalidProjectStatusError("Sprint progress must be between 0 and 100")
        if any(not item.strip() for item in self.blockers):
            raise InvalidProjectStatusError("Blockers must not include empty items")
        if any(not item.strip() for item in self.milestones_completed):
            raise InvalidProjectStatusError("Milestones must not include empty items")
        if any(not item.strip() for item in self.risks):
            raise InvalidProjectStatusError("Risks must not include empty items")