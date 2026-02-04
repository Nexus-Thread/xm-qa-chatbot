"""Structured extraction output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, TestCoverageMetrics, TimeWindow


@dataclass(frozen=True)
class ExtractionResult:
    """Container for structured data extracted from a conversation."""

    project_id: ProjectId
    time_window: TimeWindow
    test_coverage: TestCoverageMetrics | None
    overall_test_cases: int | None
