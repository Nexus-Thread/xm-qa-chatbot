"""End-to-end tests for the Gradio conversation flow."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager, ConversationSession
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitProjectDataUseCase
from qa_chatbot.application.dtos import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
from qa_chatbot.domain import (
    DomainError,
    ExtractionConfidence,
    ProjectId,
    Submission,
    SubmissionMetrics,
    TestCoverageMetrics,
    TimeWindow,
)

if TYPE_CHECKING:
    from qa_chatbot.domain.registries import StreamProjectRegistry


@dataclass
class FakeLLM:
    """Deterministic LLM adapter for testing."""

    project_confidence: ExtractionConfidence = field(default_factory=ExtractionConfidence.high)
    extract_project_error: DomainError | None = None
    extract_time_window_error: DomainError | None = None
    extract_coverage_error: DomainError | None = None

    def extract_project_id(
        self,
        conversation: str,
        registry: StreamProjectRegistry,
    ) -> tuple[ProjectId, ExtractionConfidence]:
        """Return a fixed project ID."""
        _ = conversation
        _ = registry
        if self.extract_project_error is not None:
            raise self.extract_project_error
        return ProjectId("qa-project"), self.project_confidence

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Return a fixed time window."""
        _ = conversation
        _ = current_date
        if self.extract_time_window_error is not None:
            raise self.extract_time_window_error
        return TimeWindow.from_year_month(2026, 1)

    def extract_coverage(self, conversation: str) -> CoverageExtractionResult:
        """Return fixed coverage and release-count payloads."""
        _ = conversation
        if self.extract_coverage_error is not None:
            raise self.extract_coverage_error
        return CoverageExtractionResult(
            metrics=TestCoverageMetrics(
                manual_total=10,
                automated_total=5,
                manual_created_in_reporting_month=1,
                manual_updated_in_reporting_month=1,
                automated_created_in_reporting_month=1,
                automated_updated_in_reporting_month=1,
                percentage_automation=33.33,
            ),
            supported_releases_count=2,
        )

    def extract_with_history(
        self,
        request: HistoryExtractionRequest,
        current_date: date,
        registry: StreamProjectRegistry,
    ) -> ExtractionResult:
        """Return a fixed extraction result."""
        _ = request
        _ = current_date
        _ = registry
        return ExtractionResult(
            project_id=ProjectId("qa-project"),
            time_window=TimeWindow.from_year_month(2026, 1),
            metrics=SubmissionMetrics(
                test_coverage=TestCoverageMetrics(
                    manual_total=10,
                    automated_total=5,
                    manual_created_in_reporting_month=1,
                    manual_updated_in_reporting_month=1,
                    automated_created_in_reporting_month=1,
                    automated_updated_in_reporting_month=1,
                    percentage_automation=33.33,
                ),
                overall_test_cases=None,
                supported_releases_count=2,
            ),
        )


@dataclass
class FakeStorage:
    """Capture submissions for assertions."""

    submissions: list[Submission]

    def save_submission(self, submission: Submission) -> None:
        """Store submissions in memory."""
        self.submissions.append(submission)

    def get_submissions_by_project(self, project_id: ProjectId, month: TimeWindow) -> list[Submission]:
        """Return empty results for testing."""
        _ = project_id
        _ = month
        return []

    def get_all_projects(self) -> list[ProjectId]:
        """Return empty results for testing."""
        return []

    def get_submissions_by_month(self, month: TimeWindow) -> list[Submission]:
        """Return empty results for testing."""
        _ = month
        return []

    def get_recent_months(self, limit: int) -> list[TimeWindow]:
        """Return empty results for testing."""
        _ = limit
        return []


@dataclass
class FailingStorage(FakeStorage):
    """Storage fake that fails when saving submissions."""

    def save_submission(self, submission: Submission) -> None:
        """Raise a domain error to simulate persistence failure."""
        _ = submission
        msg = "storage down"
        raise DomainError(msg)


@pytest.fixture
def conversation_manager() -> ConversationManager:
    """Provide a conversation manager with fakes."""
    extractor = ExtractStructuredDataUseCase(llm_port=FakeLLM())
    storage = FakeStorage(submissions=[])
    submitter = SubmitProjectDataUseCase(storage_port=storage)
    return ConversationManager(extractor=extractor, submitter=submitter)


def _build_manager(*, llm: FakeLLM | None = None, storage: FakeStorage | None = None) -> ConversationManager:
    extractor = ExtractStructuredDataUseCase(llm_port=llm or FakeLLM())
    submitter = SubmitProjectDataUseCase(storage_port=storage or FakeStorage(submissions=[]))
    return ConversationManager(extractor=extractor, submitter=submitter)


def test_conversation_happy_path(conversation_manager: ConversationManager) -> None:
    """Walk through the full conversation flow and save."""
    session, welcome = conversation_manager.start_session(date(2026, 1, 15))
    assert "stream/project" in welcome

    response, session = conversation_manager.handle_message("QA Project", session, date(2026, 1, 15))
    assert "reporting month" in response

    response, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))
    assert "test coverage" in response

    response, session = conversation_manager.handle_message("coverage", session, date(2026, 1, 15))
    assert "captured" in response.lower()

    response, session = conversation_manager.handle_message("yes", session, date(2026, 1, 15))
    assert "saved" in response.lower()

    assert session.state.name == "SAVED"


def test_conversation_skip_section(conversation_manager: ConversationManager) -> None:
    """Skip a section and ensure the flow continues."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))

    _, session = conversation_manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))

    response, session = conversation_manager.handle_message("skip", session, date(2026, 1, 15))
    assert "skip test coverage" in response

    response, session = conversation_manager.handle_message("yes", session, date(2026, 1, 15))
    assert "captured" in response.lower()

    assert isinstance(session, ConversationSession)


def test_edit_project_resets_dependent_sections(conversation_manager: ConversationManager) -> None:
    """Reset month and coverage when project is edited."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))

    _, session = conversation_manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("coverage", session, date(2026, 1, 15))

    response, session = conversation_manager.handle_message("project", session, date(2026, 1, 15))

    assert "stream/project" in response
    assert session.state.name == "PROJECT_ID"
    assert session.stream_project is None
    assert session.time_window is None
    assert session.test_coverage is None
    assert session.supported_releases_count is None


def test_edit_month_resets_only_month_and_coverage(conversation_manager: ConversationManager) -> None:
    """Keep project while resetting month and coverage when month is edited."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))

    _, session = conversation_manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("coverage", session, date(2026, 1, 15))
    project_before_edit = session.stream_project

    response, session = conversation_manager.handle_message("month", session, date(2026, 1, 15))

    assert "reporting month" in response
    assert session.state.name == "TIME_WINDOW"
    assert session.stream_project == project_before_edit
    assert session.time_window is None
    assert session.test_coverage is None
    assert session.supported_releases_count is None


def test_saved_state_requires_restart_keyword(conversation_manager: ConversationManager) -> None:
    """Keep saved state when restart keyword is not used."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))
    session.state = session.state.SAVED

    response, same_session = conversation_manager.handle_message("hello", session, date(2026, 1, 15))

    assert "start over" in response.lower()
    assert same_session is session
    assert same_session.state.name == "SAVED"


def test_saved_state_start_over_resets_session(conversation_manager: ConversationManager) -> None:
    """Restart should reset state and return welcome message."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))
    session.state = session.state.SAVED
    session.stream_project = ProjectId("qa-project")

    response, restarted_session = conversation_manager.handle_message("start over", session, date(2026, 1, 15))

    assert "stream/project" in response
    assert restarted_session.state.name == "PROJECT_ID"
    assert restarted_session.stream_project is None


def test_empty_message_is_rejected_without_state_change(conversation_manager: ConversationManager) -> None:
    """Reject blank input before state handlers run."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))
    state_before = session.state

    response, same_session = conversation_manager.handle_message("   ", session, date(2026, 1, 15))

    assert "please share a response" in response.lower()
    assert same_session.state == state_before


def test_medium_confidence_project_requires_confirmation() -> None:
    """Prompt for confirmation when project confidence is not high."""
    manager = _build_manager(llm=FakeLLM(project_confidence=ExtractionConfidence.medium()))
    session, _ = manager.start_session(date(2026, 1, 15))

    response, session = manager.handle_message("QA Project", session, date(2026, 1, 15))

    assert "is this correct" in response.lower()
    assert session.state.name == "PROJECT_CONFIRMATION"
    assert session.pending_project == ProjectId("qa-project")


def test_project_confirmation_negative_returns_to_project_prompt() -> None:
    """Return to project step when uncertain match is rejected."""
    manager = _build_manager(llm=FakeLLM(project_confidence=ExtractionConfidence.low()))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))

    response, session = manager.handle_message("no", session, date(2026, 1, 15))

    assert "which stream/project" in response.lower()
    assert session.state.name == "PROJECT_ID"
    assert session.pending_project is None


def test_invalid_project_input_returns_validation_error() -> None:
    """Return clear validation error for empty-like project identifiers."""
    manager = _build_manager(llm=FakeLLM(extract_project_error=DomainError("extract failed")))
    session, _ = manager.start_session(date(2026, 1, 15))

    response, session = manager.handle_message("   ", session, date(2026, 1, 15))

    assert "please share a response" in response.lower()
    assert session.state.name == "PROJECT_ID"


def test_unknown_project_returns_match_error_prompt() -> None:
    """Guide user when project format is valid but unknown."""
    manager = _build_manager(llm=FakeLLM(extract_project_error=DomainError("extract failed")))
    session, _ = manager.start_session(date(2026, 1, 15))

    response, session = manager.handle_message("some-unknown-project", session, date(2026, 1, 15))

    assert "couldn't match" in response.lower()
    assert "which stream/project" in response.lower()
    assert session.state.name == "PROJECT_ID"


def test_time_window_domain_error_reprompts_with_default() -> None:
    """Return formatted error when extractor rejects month input."""
    manager = _build_manager(llm=FakeLLM(extract_time_window_error=DomainError("bad month")))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))

    response, same_session = manager.handle_message("not-a-month", session, date(2026, 1, 15))

    assert "i ran into an issue: bad month" in response.lower()
    assert "which reporting month" in response.lower()
    assert same_session.state.name == "TIME_WINDOW"


def test_invalid_numeric_time_window_reprompts_with_error() -> None:
    """Handle invalid YYYY-MM input with an error prompt instead of crashing."""
    manager = _build_manager(llm=FakeLLM(extract_time_window_error=DomainError("bad month")))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))

    response, same_session = manager.handle_message("2026-13", session, date(2026, 1, 15))

    assert "i ran into an issue: bad month" in response.lower()
    assert "which reporting month" in response.lower()
    assert same_session.state.name == "TIME_WINDOW"


def test_test_coverage_domain_error_reprompts() -> None:
    """Return formatted error when extractor rejects coverage input."""
    manager = _build_manager(llm=FakeLLM(extract_coverage_error=DomainError("bad coverage")))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = manager.handle_message("2026-01", session, date(2026, 1, 15))

    response, same_session = manager.handle_message("coverage", session, date(2026, 1, 15))

    assert "i ran into an issue: bad coverage" in response.lower()
    assert "share test coverage" in response.lower()
    assert same_session.state.name == "TEST_COVERAGE"


def test_skip_confirmation_no_retries_section_handler() -> None:
    """Retry current section when user declines skip confirmation."""
    manager = _build_manager(llm=FakeLLM())
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = manager.handle_message("2026-01", session, date(2026, 1, 15))
    _, session = manager.handle_message("skip", session, date(2026, 1, 15))

    response, session = manager.handle_message("coverage details", session, date(2026, 1, 15))

    assert "here is what i captured" in response.lower()
    assert session.state.name == "CONFIRMATION"


def test_unknown_confirmation_edit_target_reprompts(conversation_manager: ConversationManager) -> None:
    """Ask user which section to edit when target is ambiguous."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))
    _, session = conversation_manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("coverage", session, date(2026, 1, 15))

    response, same_session = conversation_manager.handle_message("change it", session, date(2026, 1, 15))

    assert "which section should i update" in response.lower()
    assert same_session.state.name == "CONFIRMATION"


def test_save_error_in_confirmation_returns_formatted_error() -> None:
    """Return formatted error when persistence fails on confirmation."""
    manager = _build_manager(storage=FailingStorage(submissions=[]))
    session, _ = manager.start_session(date(2026, 1, 15))
    _, session = manager.handle_message("QA Project", session, date(2026, 1, 15))
    _, session = manager.handle_message("2026-01", session, date(2026, 1, 15))
    _, session = manager.handle_message("coverage", session, date(2026, 1, 15))

    response, same_session = manager.handle_message("yes", session, date(2026, 1, 15))

    assert "i ran into an issue: storage down" in response.lower()
    assert same_session.state.name == "CONFIRMATION"
