"""Edge-case tests for conversation manager branches."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, cast

import pytest

from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager, ConversationSession, ConversationState
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
from qa_chatbot.domain import (
    DomainError,
    ExtractionConfidence,
    MissingSubmissionDataError,
    ProjectId,
    Submission,
    SubmissionMetrics,
    TestCoverageMetrics,
    TimeWindow,
    build_default_stream_project_registry,
)

pytestmark = pytest.mark.e2e

if TYPE_CHECKING:
    from qa_chatbot.domain.registries import StreamProjectRegistry


@dataclass
class _FakeLLM:
    """Deterministic extraction adapter for edge-case tests."""

    extract_project_error: DomainError | None = None
    project_confidence: ExtractionConfidence = field(default_factory=ExtractionConfidence.high)

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        _ = conversation
        _ = registry
        if self.extract_project_error is not None:
            raise self.extract_project_error
        return ProjectId("qa-project"), self.project_confidence

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        _ = conversation
        _ = current_date
        return TimeWindow.from_year_month(2026, 1)

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        _ = conversation
        return CoverageExtractionResult(
            metrics=TestCoverageMetrics(manual_total=10, automated_total=5),
            supported_releases_count=2,
        )

    def extract_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        _ = request
        _ = current_date
        _ = registry
        return ExtractionResult(
            project_id=ProjectId("qa-project"),
            time_window=TimeWindow.from_year_month(2026, 1),
            metrics=SubmissionMetrics(
                test_coverage=TestCoverageMetrics(manual_total=10, automated_total=5),
                overall_test_cases=None,
                supported_releases_count=2,
            ),
        )


@dataclass
class _FakeStorage:
    """Simple in-memory storage for conversation tests."""

    submissions: list[Submission]

    def save_submission(self, submission: Submission) -> None:
        self.submissions.append(submission)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        _ = project_id
        _ = month
        return []

    def get_all_projects(self) -> list[ProjectId]:
        return []

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        _ = month
        return []

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        _ = limit
        return []


def _build_manager(*, llm: _FakeLLM | None = None) -> ConversationManager:
    extractor = ExtractStructuredDataUseCase(llm_port=llm or _FakeLLM())
    submitter = SubmitProjectDataUseCase(storage_port=_FakeStorage(submissions=[]))
    return ConversationManager(
        extractor=extractor,
        submitter=submitter,
        registry=build_default_stream_project_registry(),
    )


def test_unknown_state_returns_formatted_error() -> None:
    """Return an error response when a session enters an unsupported state."""
    manager = _build_manager()
    session = ConversationSession(state=cast("ConversationState", "invalid-state"))

    response, same_session = manager.handle_message("hello", session, date(2026, 1, 15))

    assert "unknown state" in response.lower()
    assert same_session is session


def test_project_fallback_uses_registry_match_when_llm_fails() -> None:
    """Use registry lookup when project extraction fails but user input matches known project."""
    manager = _build_manager(llm=_FakeLLM(extract_project_error=DomainError("extract failed")))
    session, _ = manager.start_session(date(2026, 1, 15))

    response, session = manager.handle_message("client_trading", session, date(2026, 1, 15))

    assert session.state == ConversationState.TIME_WINDOW
    assert session.stream_project == ProjectId("client_trading")
    assert "which reporting month" in response.lower()


def test_project_confirmation_affirmative_advances_to_time_window() -> None:
    """Advance from project confirmation when user accepts uncertain project match."""
    manager = _build_manager(llm=_FakeLLM(project_confidence=ExtractionConfidence.low()))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("qa project", session, date(2026, 1, 15))

    response, session = manager.handle_message("yes", session, date(2026, 1, 15))

    assert session.state == ConversationState.TIME_WINDOW
    assert session.pending_project is None
    assert session.pending_confidence is None
    assert "which reporting month" in response.lower()


def test_skip_confirmation_without_pending_section_returns_missing_data_prompt() -> None:
    """Handle skip-confirmation state without pending section by returning confirmation error summary."""
    manager = _build_manager()
    session = ConversationSession(state=ConversationState.SKIP_CONFIRMATION)

    response, same_session = manager.handle_message("yes", session, date(2026, 1, 15))

    assert "missing stream/project or month information" in response.lower()
    assert same_session.state == ConversationState.CONFIRMATION


def test_confirmation_edit_coverage_prompts_for_test_coverage() -> None:
    """Prompt for test coverage when user asks to edit coverage in confirmation state."""
    manager = _build_manager()
    session = ConversationSession(
        state=ConversationState.CONFIRMATION,
        stream_project=ProjectId("qa-project"),
        time_window=TimeWindow.from_year_month(2026, 1),
        test_coverage=TestCoverageMetrics(manual_total=1, automated_total=1),
    )

    response, same_session = manager.handle_message("change test coverage", session, date(2026, 1, 15))

    assert same_session.state == ConversationState.TEST_COVERAGE
    assert "share test coverage" in response.lower()


def test_time_window_parser_handles_current_and_previous_aliases() -> None:
    """Parse simple month aliases without calling extraction adapter."""
    manager = _build_manager()
    session = ConversationSession(state=ConversationState.TIME_WINDOW, stream_project=ProjectId("qa-project"))

    response_current, current_session = manager.handle_message("current", session, date(2026, 2, 3))
    assert current_session.time_window == TimeWindow.from_year_month(2026, 1)
    assert current_session.state == ConversationState.TEST_COVERAGE
    assert "share test coverage" in response_current.lower()

    session_previous = ConversationSession(state=ConversationState.TIME_WINDOW, stream_project=ProjectId("qa-project"))
    response_previous, previous_session = manager.handle_message("last month", session_previous, date(2026, 2, 3))

    assert previous_session.time_window == TimeWindow.from_year_month(2026, 1)
    assert previous_session.state == ConversationState.TEST_COVERAGE
    assert "share test coverage" in response_previous.lower()


def test_build_command_raises_when_required_fields_are_missing() -> None:
    """Raise an explicit domain error when trying to build command without project/month."""
    manager = _build_manager()

    with pytest.raises(MissingSubmissionDataError, match="Stream/project and reporting month are required"):
        manager._build_command(ConversationSession())  # noqa: SLF001

    with pytest.raises(MissingSubmissionDataError, match="Stream/project and reporting month are required"):
        manager._submitter_command(ConversationSession(), raw_conversation="history")  # noqa: SLF001
