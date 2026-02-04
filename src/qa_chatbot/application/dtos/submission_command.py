"""Submission command payload."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

    from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow


@dataclass(frozen=True)
class SubmissionCommand:
    """Input data for submitting team metrics."""

    project_id: ProjectId
    time_window: TimeWindow
    test_coverage: TestCoverageMetrics | None
    overall_test_cases: int | None
    raw_conversation: str | None = None
    created_at: datetime | None = None
