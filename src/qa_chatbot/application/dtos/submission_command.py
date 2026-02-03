"""Submission command payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, TeamId, TimeWindow


@dataclass(frozen=True)
class SubmissionCommand:
    """Input data for submitting team metrics."""

    team_id: TeamId
    time_window: TimeWindow
    qa_metrics: QAMetrics | None
    project_status: ProjectStatus | None
    daily_update: DailyUpdate | None
    raw_conversation: str | None = None
    created_at: datetime | None = None
