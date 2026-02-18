"""Structured extraction output."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.domain import ProjectId, SubmissionMetrics, TestCoverageMetrics, TimeWindow


@dataclass(frozen=True)
class CoverageExtractionResult:
    """Container for extracted coverage metrics."""

    metrics: TestCoverageMetrics
    supported_releases_count: int | None


@dataclass(frozen=True)
class HistoryExtractionRequest:
    """Input payload for selective history-based extraction."""

    conversation: str
    history: list[dict[str, str]] | None = None
    known_project_id: ProjectId | None = None
    known_time_window: TimeWindow | None = None
    known_test_coverage: TestCoverageMetrics | None = None
    known_supported_releases_count: int | None = None
    include_project_id: bool = True
    include_time_window: bool = True
    include_test_coverage: bool = True
    include_supported_releases_count: bool = True


@dataclass(frozen=True)
class ExtractionResult:
    """Container for structured data extracted from a conversation."""

    project_id: ProjectId
    time_window: TimeWindow
    metrics: SubmissionMetrics
