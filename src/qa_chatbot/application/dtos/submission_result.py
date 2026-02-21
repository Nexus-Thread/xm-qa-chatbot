"""Submission result DTO for persisted updates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain import Submission


@dataclass(frozen=True)
class SubmissionResult:
    """Represent persisted submission outcome with optional warnings."""

    submission: Submission
    warnings: tuple[str, ...] = ()

    @property
    def has_warnings(self) -> bool:
        """Return whether submission completed with warnings."""
        return bool(self.warnings)
