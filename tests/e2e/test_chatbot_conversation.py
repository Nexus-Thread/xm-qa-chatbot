"""End-to-end tests for the Gradio conversation flow."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pytest

from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager, ConversationSession
from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase
from qa_chatbot.application.dtos import ExtractionResult
from qa_chatbot.domain import DailyUpdate, ProjectStatus, QAMetrics, Submission, TeamId, TimeWindow


@dataclass
class FakeLLM:
    """Deterministic LLM adapter for testing."""

    def extract_team_id(self, conversation: str) -> TeamId:
        """Return a fixed team ID."""
        _ = conversation
        return TeamId("QA Team")

    def extract_time_window(self, conversation: str, current_date: date) -> TimeWindow:
        """Return a fixed time window."""
        _ = conversation
        _ = current_date
        return TimeWindow.from_year_month(2026, 1)

    def extract_qa_metrics(self, conversation: str) -> QAMetrics:
        """Return a fixed QA metrics payload."""
        _ = conversation
        return QAMetrics(tests_passed=10, tests_failed=2, test_coverage_percent=92.0)

    def extract_project_status(self, conversation: str) -> ProjectStatus:
        """Return a fixed project status payload."""
        _ = conversation
        return ProjectStatus(sprint_progress_percent=75.0, blockers=("None",))

    def extract_daily_update(self, conversation: str) -> DailyUpdate:
        """Return a fixed daily update payload."""
        _ = conversation
        return DailyUpdate(completed_tasks=("Fixed bugs",), planned_tasks=("Release",))

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
            team_id=TeamId("QA Team"),
            time_window=TimeWindow.from_year_month(2026, 1),
            qa_metrics=None,
            project_status=None,
            daily_update=None,
        )


@dataclass
class FakeStorage:
    """Capture submissions for assertions."""

    submissions: list[Submission]

    def save_submission(self, submission: Submission) -> None:
        """Store submissions in memory."""
        self.submissions.append(submission)

    def get_submissions_by_team(self, team_id: TeamId, month: TimeWindow) -> list[Submission]:
        """Return empty results for testing."""
        _ = team_id
        _ = month
        return []

    def get_all_teams(self) -> list[TeamId]:
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
    assert "Which team" in welcome

    response, session = conversation_manager.handle_message("QA Team", session, date(2026, 1, 15))
    assert "reporting month" in response

    response, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))
    assert "QA metrics" in response

    response, session = conversation_manager.handle_message("metrics", session, date(2026, 1, 15))
    assert "project status" in response

    response, session = conversation_manager.handle_message("status", session, date(2026, 1, 15))
    assert "daily updates" in response

    response, session = conversation_manager.handle_message("updates", session, date(2026, 1, 15))
    assert "Here is what I captured" in response

    response, session = conversation_manager.handle_message("yes", session, date(2026, 1, 15))
    assert "saved" in response.lower()

    assert session.state.name == "SAVED"


def test_conversation_skip_section(conversation_manager: ConversationManager) -> None:
    """Skip a section and ensure the flow continues."""
    session, _ = conversation_manager.start_session(date(2026, 1, 15))

    _, session = conversation_manager.handle_message("QA Team", session, date(2026, 1, 15))
    _, session = conversation_manager.handle_message("2026-01", session, date(2026, 1, 15))

    response, session = conversation_manager.handle_message("skip", session, date(2026, 1, 15))
    assert "skip QA metrics" in response

    response, session = conversation_manager.handle_message("yes", session, date(2026, 1, 15))
    assert "project status" in response

    assert isinstance(session, ConversationSession)
