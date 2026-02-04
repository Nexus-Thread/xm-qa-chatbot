"""Project status value object."""

from __future__ import annotations

from dataclasses import dataclass, field

from qa_chatbot.domain.exceptions import InvalidProjectStatusError


@dataclass(frozen=True)
class ProjectStatus:
    """Project tracking information for a reporting window."""

    sprint_progress_percent: float | None = None
    blockers: tuple[str, ...] = field(default_factory=tuple)
    milestones_completed: tuple[str, ...] = field(default_factory=tuple)
    risks: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate project status values."""
        self._ensure_non_empty_items(self.blockers, "Blockers")
        self._ensure_non_empty_items(self.milestones_completed, "Milestones")
        self._ensure_non_empty_items(self.risks, "Risks")
        if self.sprint_progress_percent is not None and not 0 <= self.sprint_progress_percent <= 100:
            msg = "Sprint progress must be between 0 and 100"
            raise InvalidProjectStatusError(msg)

    @staticmethod
    def _ensure_non_empty_items(items: tuple[str, ...], label: str) -> None:
        """Ensure each entry is non-empty after trimming."""
        if any(not item.strip() for item in items):
            msg = f"{label} must not include empty items"
            raise InvalidProjectStatusError(msg)
