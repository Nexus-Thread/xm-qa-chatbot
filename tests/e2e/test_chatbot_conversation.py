"""End-to-end tests for the Gradio conversation flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager, ConversationSession
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase
from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow

if TYPE_CHECKING:
    from qa_chatbot.domain.registries import StreamRegistry


@dataclass
class FakeLLM:
    """Deterministic LLM adapter for testing."""

    def extract_project_id(self, conversation: str, registry: StreamRegistry) -> tuple[ProjectId, str]:
        """Return a fixed project ID."""
        _ = conversation
        _ = registry
        return ProjectId("qa-project"), "high"

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Return a fixed time window."""
        _ = conversation
        _ = current_date
        return TimeWindow.from_year_month(2026, 1)

    def extract_test_coverage(self, conversation: str) -> TestCoverageMetrics:
        """Return a fixed coverage payload."""
        _ = conversation
        return TestCoverageMetrics(
            manual_total=10,
            automated_total=5,
            manual_created_last_month=1,
            manual_updated_last_month=1,
            automated_created_last_month=1,
            automated_updated_last_month=1,
            percentage_automation=33.33,
        )

    def extract_supported_releases_count(self, conversation: str) -> int | None:
        """Return a fixed supported releases count."""
        _ = conversation
        return 2

    def extract_with_history(
        self,
        conversation: str,
        history: list[dict[str, str]] | None,
        current_date: date,
    ) -> ExtractionResult:
        """Return a fixed extraction result."""
        _ = conversation
        _ = history
        _ = current_date
        return ExtractionResult(
            project_id=ProjectId("qa-project"),
            time_window=TimeWindow.from_year_month(2026, 1),
            test_coverage=TestCoverageMetrics(
                manual_total=10,
                automated_total=5,
                manual_created_last_month=1,
                manual_updated_last_month=1,
                automated_created_last_month=1,
                automated_updated_last_month=1,
                percentage_automation=33.33,
            ),
            overall_test_cases=None,
            supported_releases_count=2,
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


@pytest.fixture
def conversation_manager() -> ConversationManager:
    """Provide a conversation manager with fakes."""
    extractor = ExtractStructuredDataUseCase(llm_port=FakeLLM())
    storage = FakeStorage(submissions=[])
    submitter = SubmitTeamDataUseCase(storage_port=storage)
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

    _, session = conversation_manager.handle_message("QA Team", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))

    response, session = conversation_manager.handle_message("skip", session, date(2026, 1, 15))
    assert "skip test coverage" in response

    response, session = conversation_manager.handle_message("yes", session, date(2026, 1, 15))
    assert "captured" in response.lower()

    assert isinstance(session, ConversationSession)
