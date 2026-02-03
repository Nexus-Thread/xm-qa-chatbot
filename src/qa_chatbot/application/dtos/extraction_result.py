"""Structured extraction output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


@dataclass(frozen=True)
class ExtractionResult:
    """Container for structured data extracted from a conversation."""

    team_id: TeamId
    time_window: TimeWindow
    qa_metrics: QAMetrics | None
    project_status: ProjectStatus | None
    daily_update: DailyUpdate | None
