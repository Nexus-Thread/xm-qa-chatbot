"""Daily update value object."""

from __future__ import annotations

from dataclasses import dataclass, field

from qa_chatbot.domain.exceptions import InvalidDailyUpdateError


@dataclass(frozen=True)
class DailyUpdate:
    """Daily status update for a reporting window."""

    completed_tasks: tuple[str, ...] = field(default_factory=tuple)
    planned_tasks: tuple[str, ...] = field(default_factory=tuple)
    capacity_hours: float | None = None
    issues: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        """Validate daily update values."""
        self._ensure_non_empty_items(self.completed_tasks, "Completed tasks")
        self._ensure_non_empty_items(self.planned_tasks, "Planned tasks")
        self._ensure_non_empty_items(self.issues, "Issues")
        if self.capacity_hours is not None and self.capacity_hours < 0:
            msg = "Capacity hours must be non-negative"
            raise InvalidDailyUpdateError(msg)

    @staticmethod
    def _ensure_non_empty_items(items: tuple[str, ...], label: str) -> None:
        """Ensure each entry is non-empty after trimming."""
        if any(not item.strip() for item in items):
            msg = f"{label} must not include empty items"
            raise InvalidDailyUpdateError(msg)
