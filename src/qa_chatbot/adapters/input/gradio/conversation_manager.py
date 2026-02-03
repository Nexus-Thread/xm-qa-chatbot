"""Conversation state management for the Gradio chatbot."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from qa_chatbot.adapters.input.gradio import formatters
from qa_chatbot.domain import DomainError, MissingSubmissionDataError, TeamId, TimeWindow

if TYPE_CHECKING:
    from datetime import date

    from qa_chatbot.application import ExtractStructuredDataUseCase, SubmitTeamDataUseCase
    from qa_chatbot.application.dtos import SubmissionCommand
    from qa_chatbot.domain.value_objects import DailyUpdate, ProjectStatus, QAMetrics


class ConversationState(StrEnum):
    """Supported conversation states."""

    TEAM_ID = "team_id"
    TIME_WINDOW = "time_window"
    QA_METRICS = "qa_metrics"
    PROJECT_STATUS = "project_status"
    DAILY_UPDATE = "daily_update"
    SKIP_CONFIRMATION = "skip_confirmation"
    CONFIRMATION = "confirmation"
    SAVED = "saved"


@dataclass
class ConversationSession:
    """Conversation session state."""

    state: ConversationState = ConversationState.TEAM_ID
    team_id: TeamId | None = None
    time_window: TimeWindow | None = None
    qa_metrics: QAMetrics | None = None
    project_status: ProjectStatus | None = None
    daily_update: DailyUpdate | None = None
    pending_section: ConversationState | None = None
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
            ConversationState.TEAM_ID: self._handle_team_id,
            ConversationState.TIME_WINDOW: self._handle_time_window,
            ConversationState.QA_METRICS: self._handle_qa_metrics,
            ConversationState.PROJECT_STATUS: self._handle_project_status,
            ConversationState.DAILY_UPDATE: self._handle_daily_update,
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

    def _handle_team_id(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle team identification."""
        try:
            team_id = self._extractor.extract_team_id(message)
            session.team_id = team_id
        except DomainError:
            try:
                session.team_id = TeamId.from_raw(message)
            except DomainError as err:
                return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_team_id()

        session.state = ConversationState.TIME_WINDOW
        default_window = TimeWindow.default_for(today)
        return formatters.prompt_for_time_window(default_window)

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
        session.state = ConversationState.QA_METRICS
        return formatters.prompt_for_qa_metrics()

    def _handle_qa_metrics(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle QA metrics collection."""
        _ = today
        if self._is_skip_request(message):
            return self._request_skip_confirmation(session, ConversationState.QA_METRICS, "QA metrics")
        try:
            session.qa_metrics = self._extractor.extract_qa_metrics(message)
        except DomainError as err:
            return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_qa_metrics()

        session.state = ConversationState.PROJECT_STATUS
        return formatters.prompt_for_project_status()

    def _handle_project_status(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle project status collection."""
        _ = today
        if self._is_skip_request(message):
            return self._request_skip_confirmation(session, ConversationState.PROJECT_STATUS, "project status")
        try:
            session.project_status = self._extractor.extract_project_status(message)
        except DomainError as err:
            return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_project_status()

        session.state = ConversationState.DAILY_UPDATE
        return formatters.prompt_for_daily_update()

    def _handle_daily_update(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle daily update collection."""
        _ = today
        if self._is_skip_request(message):
            return self._request_skip_confirmation(session, ConversationState.DAILY_UPDATE, "daily updates")
        try:
            session.daily_update = self._extractor.extract_daily_update(message)
        except DomainError as err:
            return formatters.format_error_message(str(err)) + " " + formatters.prompt_for_daily_update()

        session.state = ConversationState.CONFIRMATION
        return self._build_confirmation_prompt(session)

    def _handle_skip_confirmation(self, message: str, session: ConversationSession, today: date) -> str:
        """Handle confirmation for skipping a section."""
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
            if not self._has_any_section(session):
                session.state = ConversationState.QA_METRICS
                return "I need at least one data section to save your submission. " + formatters.prompt_for_qa_metrics()

            try:
                self._submitter.execute(self._build_command(session))
            except DomainError as err:
                return formatters.format_error_message(str(err))

            session.state = ConversationState.SAVED
            return formatters.format_saved_message()

        target_state = self._detect_edit_target(message)
        if target_state is None:
            return (
                "Which section should I update? You can say team, month, QA metrics, project status, or daily update."
            )

        self._reset_section(session, target_state)
        session.state = target_state
        return self._prompt_for_state(target_state, today)

    def _build_confirmation_prompt(self, session: ConversationSession) -> str:
        """Construct the confirmation prompt."""
        if session.team_id is None or session.time_window is None:
            return formatters.format_error_message("Missing team or month information.")

        summary = formatters.format_submission_summary(
            team_id=session.team_id,
            time_window=session.time_window,
            qa_metrics=session.qa_metrics,
            project_status=session.project_status,
            daily_update=session.daily_update,
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
        if section == ConversationState.QA_METRICS:
            session.state = ConversationState.PROJECT_STATUS
            return formatters.prompt_for_project_status()
        if section == ConversationState.PROJECT_STATUS:
            session.state = ConversationState.DAILY_UPDATE
            return formatters.prompt_for_daily_update()
        if section == ConversationState.DAILY_UPDATE:
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
            ConversationState.QA_METRICS: self._handle_qa_metrics,
            ConversationState.PROJECT_STATUS: self._handle_project_status,
            ConversationState.DAILY_UPDATE: self._handle_daily_update,
        }.get(session.state)
        if handler is None:
            return formatters.format_error_message("Unable to resume section.")
        return handler(message, session, today)

    def _prompt_for_state(self, state: ConversationState, today: date) -> str:
        """Return the prompt text for a state."""
        if state == ConversationState.TEAM_ID:
            return formatters.prompt_for_team_id()
        if state == ConversationState.TIME_WINDOW:
            return formatters.prompt_for_time_window(TimeWindow.default_for(today))
        if state == ConversationState.QA_METRICS:
            return formatters.prompt_for_qa_metrics()
        if state == ConversationState.PROJECT_STATUS:
            return formatters.prompt_for_project_status()
        if state == ConversationState.DAILY_UPDATE:
            return formatters.prompt_for_daily_update()
        return "Please share the update."

    def _detect_edit_target(self, message: str) -> ConversationState | None:
        """Detect which section the user wants to edit."""
        normalized = message.lower()
        if "team" in normalized:
            return ConversationState.TEAM_ID
        if "month" in normalized or "time" in normalized:
            return ConversationState.TIME_WINDOW
        if "qa" in normalized or "test" in normalized or "bug" in normalized:
            return ConversationState.QA_METRICS
        if "project" in normalized or "blocker" in normalized or "milestone" in normalized:
            return ConversationState.PROJECT_STATUS
        if "daily" in normalized or "today" in normalized or "update" in normalized:
            return ConversationState.DAILY_UPDATE
        return None

    def _reset_section(self, session: ConversationSession, section: ConversationState) -> None:
        """Reset stored values for a section."""
        if section == ConversationState.TEAM_ID:
            session.team_id = None
        elif section == ConversationState.TIME_WINDOW:
            session.time_window = None
        elif section == ConversationState.QA_METRICS:
            session.qa_metrics = None
        elif section == ConversationState.PROJECT_STATUS:
            session.project_status = None
        elif section == ConversationState.DAILY_UPDATE:
            session.daily_update = None

    def _has_any_section(self, session: ConversationSession) -> bool:
        """Return whether any data section is present."""
        return any([session.qa_metrics, session.project_status, session.daily_update])

    def _build_command(self, session: ConversationSession) -> SubmissionCommand:
        """Build a submission command from session data."""
        raw_conversation = self._build_raw_conversation(session)
        if session.team_id is None or session.time_window is None:
            msg = "Team ID and reporting month are required."
            raise MissingSubmissionDataError(msg)

        return self._submitter_command(session, raw_conversation)

    @staticmethod
    def _submitter_command(session: ConversationSession, raw_conversation: str | None) -> SubmissionCommand:
        """Create a SubmissionCommand instance."""
        from qa_chatbot.application.dtos import SubmissionCommand

        if session.team_id is None or session.time_window is None:
            msg = "Team ID and reporting month are required."
            raise MissingSubmissionDataError(msg)

        return SubmissionCommand(
            team_id=session.team_id,
            time_window=session.time_window,
            qa_metrics=session.qa_metrics,
            project_status=session.project_status,
            daily_update=session.daily_update,
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
        session.team_id = new_session.team_id
        session.time_window = new_session.time_window
        session.qa_metrics = new_session.qa_metrics
        session.project_status = new_session.project_status
        session.daily_update = new_session.daily_update
        session.pending_section = new_session.pending_section
        session.history = new_session.history
        return welcome, session
