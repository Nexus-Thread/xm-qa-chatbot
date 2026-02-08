"""Conversation state management for the Gradio chatbot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from qa_chatbot.adapters.input.gradio import formatters
from qa_chatbot.domain import DomainError, MissingSubmissionDataError, ProjectId, TimeWindow, build_default_registry

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.domain.value_objects import TestCoverageMetrics


class ConversationState(StrEnum):
    """Supported conversation states."""

    PROJECT_ID = "project_id"
    PROJECT_CONFIRMATION = "project_confirmation"
    TIME_WINDOW = "time_window"
    TEST_COVERAGE = "test_coverage"
    SKIP_CONFIRMATION = "skip_confirmation"
    CONFIRMATION = "confirmation"
    SAVED = "saved"


@dataclass
class ConversationSession:
    """Conversation session state."""

    state: ConversationState = ConversationState.PROJECT_ID
    stream_project: ProjectId | None = None
    time_window: TimeWindow | None = None
    test_coverage: TestCoverageMetrics | None = None
    pending_section: ConversationState | None = None
    pending_project: ProjectId | None = None
    history: list[dict[str, str]] = field(default_factory=list)


class ConversationManager:
    """Manage multi-step conversation flow."""

    def __init__(
        self,
        extractor: ExtractStructuredDataUseCase,
        submitter: SubmitTeamDataUseCase,
    ) -> None:
        """Initialize the conversation manager."""
        self._extractor = extractor
        self._submitter = submitter

    def start_session(self, today: date) -> tuple[ConversationSession, str]:
        """Start a new conversation session."""
        session = ConversationSession()
        welcome = formatters.welcome_message(today)
        self._append_history(session, role="assistant", content=welcome)
        return session, welcome

    def handle_message(
        self,
        message: str,
        session: ConversationSession,
        today: date,
    ) -> tuple[str, ConversationSession]:
        """Handle an incoming user message."""
        normalized = message.strip()
        if not normalized:
            response = "Please share a response so I can continue."
            return response, session

        if session.state == ConversationState.SAVED:
            if self._is_restart_request(normalized):
                return self._restart_session(session, today)
            response = "Your submission is saved. Reply with 'start over' to submit another update."
            self._append_history(session, role="assistant", content=response)
            return response, session

        self._append_history(session, role="user", content=normalized)

        handlers = {
            ConversationState.PROJECT_ID: self._handle_project_id,
            ConversationState.PROJECT_CONFIRMATION: self._handle_project_confirmation,
            ConversationState.TIME_WINDOW: self._handle_time_window,
            ConversationState.TEST_COVERAGE: self._handle_test_coverage,
            ConversationState.SKIP_CONFIRMATION: self._handle_skip_confirmation,
            ConversationState.CONFIRMATION: self._handle_confirmation,
        }
        handler = handlers.get(session.state)
        if handler is None:
            response = formatters.format_error_message("Conversation is in an unknown state.")
            self._append_history(session, role="assistant", content=response)
            return response, session

        response = handler(normalized, session, today)
        self._append_history(session, role="assistant", content=response)
        return response, session

    def _handle_project_id(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle project identification."""
        registry = build_default_registry()

        try:
            project_id, confidence = self._extractor.extract_project_id(message, registry)

            if confidence == "high":
                session.stream_project = project_id
                session.state = ConversationState.TIME_WINDOW
                default_window = TimeWindow.default_for(today)
                return formatters.prompt_for_time_window(default_window)

            session.pending_project = project_id
            session.state = ConversationState.PROJECT_CONFIRMATION
            project = registry.find_project(project_id.value)
            project_name = project.name if project else project_id.value
            return formatters.format_project_confirmation(project_name)

        except DomainError:
            project = registry.find_project(message)
            if project is None:
                try:
                    ProjectId.from_raw(message)
                    return (
                        formatters.format_error_message("I couldn't match that to a known project.")
                        + " "
                        + formatters.prompt_for_project()
                    )
                except DomainError as err:
                    return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_project()

            session.stream_project = ProjectId.from_raw(project.id)
            session.state = ConversationState.TIME_WINDOW
            default_window = TimeWindow.default_for(today)
            return formatters.prompt_for_time_window(default_window)

    def _handle_project_confirmation(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle confirmation of uncertain project matching."""
        if self._is_affirmative(message) and session.pending_project is not None:
            session.stream_project = session.pending_project
            session.pending_project = None
            session.state = ConversationState.TIME_WINDOW
            default_window = TimeWindow.default_for(today)
            return formatters.prompt_for_time_window(default_window)

        session.pending_project = None
        session.state = ConversationState.PROJECT_ID
        return "No problem. " + formatters.prompt_for_project()

    def _handle_time_window(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle time window selection."""
        parsed_window = self._parse_time_window(message, today)
        if parsed_window is None:
            try:
                parsed_window = self._extractor.extract_time_window(message, today)
            except DomainError as err:
                default_window = TimeWindow.default_for(today)
                return (
                    formatters.format_error_message(str(err)) + " " + formatters.prompt_for_time_window(default_window)
                )

        session.time_window = parsed_window
        session.state = ConversationState.TEST_COVERAGE
        return formatters.prompt_for_test_coverage()

    def _handle_test_coverage(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle test coverage collection."""
        _ = today
        if self._is_skip_request(message):
            return self._request_skip_confirmation(session, ConversationState.TEST_COVERAGE, "test coverage")
        try:
            session.test_coverage = self._extractor.extract_test_coverage(message)
        except DomainError as err:
            return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_test_coverage()

        session.state = ConversationState.CONFIRMATION
        return self._build_confirmation_prompt(session)

    def _handle_skip_confirmation(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle confirmation for skipping a section."""
        _ = today
        pending = session.pending_section
        if pending is None:
            session.state = ConversationState.CONFIRMATION
            return self._build_confirmation_prompt(session)

        if self._is_affirmative(message):
            session.pending_section = None
            return self._advance_from_section(session, pending, today)

        session.pending_section = None
        session.state = pending
        return self._handle_message_for_section(message, session, today)

    def _handle_confirmation(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle final confirmation and persistence."""
        if self._is_affirmative(message):
            try:
                self._submitter.execute(self._build_command(session))
            except DomainError as err:
                return formatters.format_error_message(str(err))

            session.state = ConversationState.SAVED
            return formatters.format_saved_message()

        target_state = self._detect_edit_target(message)
        if target_state is None:
            return "Which section should I update? You can say project, month, or test coverage."

        self._reset_section(session, target_state)
        session.state = target_state
        return self._prompt_for_state(target_state, today)

    def _build_confirmation_prompt(self, session: ConversationSession) -> str:
        """Construct the confirmation prompt."""
        if session.stream_project is None or session.time_window is None:
            return formatters.format_error_message("Missing stream/project or month information.")

        summary = formatters.format_submission_summary(
            project_id=session.stream_project,
            time_window=session.time_window,
            test_coverage=session.test_coverage,
            overall_test_cases=None,
        )
        return formatters.prompt_for_confirmation(summary)

    def _request_skip_confirmation(
        self,
        session: ConversationSession,
        section: ConversationState,
        label: str,
    ) -> str:
        """Ask for confirmation before skipping a section."""
        session.pending_section = section
        session.state = ConversationState.SKIP_CONFIRMATION
        return formatters.format_skip_confirmation(label)

    def _advance_from_section(
        self,
        session: ConversationSession,
        section: ConversationState,
        today: date,
    ) -> str:
        """Move to the next state after a section is handled."""
        _ = today
        if section == ConversationState.TEST_COVERAGE:
            session.state = ConversationState.CONFIRMATION
            return self._build_confirmation_prompt(session)

        session.state = ConversationState.CONFIRMATION
        return self._build_confirmation_prompt(session)

    def _handle_message_for_section(
        self,
        message: str,
        session: ConversationSession,
        today: date,
    ) -> str:
        """Handle message when returning from skip confirmation."""
        handler = {
            ConversationState.TEST_COVERAGE: self._handle_test_coverage,
        }.get(session.state)
        if handler is None:
            return formatters.format_error_message("Unable to resume section.")
        return handler(message, session, today)

    def _prompt_for_state(self, state: ConversationState, today: date) -> str:
        """Return the prompt text for a state."""
        if state == ConversationState.PROJECT_ID:
            return formatters.prompt_for_project()
        if state == ConversationState.TIME_WINDOW:
            return formatters.prompt_for_time_window(TimeWindow.default_for(today))
        if state == ConversationState.TEST_COVERAGE:
            return formatters.prompt_for_test_coverage()
        return "Please share the update."

    def _detect_edit_target(self, message: str) -> ConversationState | None:
        """Detect which section the user wants to edit."""
        normalized = message.lower()
        if "project" in normalized:
            return ConversationState.PROJECT_ID
        if "month" in normalized or "time" in normalized:
            return ConversationState.TIME_WINDOW
        if "coverage" in normalized or "test" in normalized:
            return ConversationState.TEST_COVERAGE
        return None

    def _reset_section(self, session: ConversationSession, section: ConversationState) -> None:
        """Reset stored values for a section."""
        if section == ConversationState.PROJECT_ID:
            session.stream_project = None
        elif section == ConversationState.TIME_WINDOW:
            session.time_window = None
        elif section == ConversationState.TEST_COVERAGE:
            session.test_coverage = None

    def _build_command(self, session: ConversationSession) -> SubmissionCommand:
        """Build a submission command from session data."""
        raw_conversation = self._build_raw_conversation(session)
        if session.stream_project is None or session.time_window is None:
            msg = "Stream/project and reporting month are required."
            raise MissingSubmissionDataError(msg)

        return self._submitter_command(session, raw_conversation)

    @staticmethod
    def _submitter_command(session: ConversationSession, raw_conversation: str | None) -> SubmissionCommand:
        """Create a SubmissionCommand instance."""
        from qa_chatbot.application.dtos import SubmissionCommand

        if session.stream_project is None or session.time_window is None:
            msg = "Stream/project and reporting month are required."
            raise MissingSubmissionDataError(msg)

        return SubmissionCommand(
            project_id=session.stream_project,
            time_window=session.time_window,
            test_coverage=session.test_coverage,
            overall_test_cases=None,
            raw_conversation=raw_conversation,
        )

    @staticmethod
    def _append_history(session: ConversationSession, *, role: str, content: str) -> None:
        """Append a message to the session history."""
        session.history.append({"role": role, "content": content})

    @staticmethod
    def _build_raw_conversation(session: ConversationSession) -> str:
        """Serialize conversation history for persistence."""
        lines = []
        for entry in session.history:
            role = entry.get("role", "user").capitalize()
            content = entry.get("content", "")
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines)

    @staticmethod
    def _is_affirmative(message: str) -> bool:
        """Return whether the message is an affirmative response."""
        return message.strip().lower() in {"yes", "y", "yep", "sure", "confirm", "ok", "okay"}

    @staticmethod
    def _is_skip_request(message: str) -> bool:
        """Return whether the user wants to skip a section."""
        normalized = message.strip().lower()
        return normalized in {"skip", "no", "none", "n/a", "na", "nothing"}

    @staticmethod
    def _is_restart_request(message: str) -> bool:
        """Return whether the user wants to restart."""
        normalized = message.strip().lower()
        return normalized in {"start", "start over", "restart", "new"}

    @staticmethod
    def _parse_time_window(message: str, today: date) -> TimeWindow | None:
        """Try to parse a time window from simple inputs."""
        normalized = message.strip().lower()
        if normalized in {"default", "current", "current month", "this month"}:
            return TimeWindow.default_for(today)
        if normalized in {"previous", "last month", "previous month"}:
            return TimeWindow.default_for(today, grace_period_days=31)

        if "-" in normalized:
            parts = normalized.split("-")
            if len(parts) == 2:
                try:
                    year = int(parts[0])
                    month = int(parts[1])
                    return TimeWindow.from_year_month(year, month)
                except ValueError:
                    return None
        return None

    def _restart_session(self, session: ConversationSession, today: date) -> tuple[str, ConversationSession]:
        """Restart the session after saving."""
        new_session, welcome = self.start_session(today)
        session.state = new_session.state
        session.stream_project = new_session.stream_project
        session.time_window = new_session.time_window
        session.test_coverage = new_session.test_coverage
        session.pending_section = new_session.pending_section
        session.history = new_session.history
        return welcome, session
