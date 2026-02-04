"""Gradio adapter for chat-based data collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime

import gradio as gr

from .conversation_manager import ConversationManager, ConversationSession  # noqa: TC001


@dataclass(frozen=True)
class GradioSettings:
    """Settings for configuring the Gradio server."""

    server_port: int = 7860
    share: bool = False
    input_max_chars: int = 2000
    rate_limit_requests: int = 8
    rate_limit_window_seconds: int = 60


class GradioAdapter:
    """Gradio UI adapter for the QA chatbot."""

    def __init__(self, manager: ConversationManager, settings: GradioSettings | None = None) -> None:
        """Initialize the Gradio adapter."""
        self._manager = manager
        self._settings = settings or GradioSettings()
        self._rate_limiter = _RateLimiter(
            max_requests=self._settings.rate_limit_requests,
            window_seconds=self._settings.rate_limit_window_seconds,
        )

    def launch(self) -> None:
        """Launch the Gradio server."""
        app = self._build_ui()
        app.launch(server_port=self._settings.server_port, share=self._settings.share)

    def _build_ui(self) -> gr.Blocks:
        """Build the Gradio UI blocks."""
        with gr.Blocks() as app:
            gr.Markdown("# XM QA Chatbot")
            gr.Markdown("Share your QA metrics and project updates below.")

            session_state = gr.State()
            chat_history = gr.Chatbot(height=460)
            user_input = gr.Textbox(
                placeholder="Type your update here...",
                container=False,
            )
            reset_button = gr.Button("Start Over")

            def initialize() -> tuple[ConversationSession, list[dict[str, str]]]:
                session, welcome = self._manager.start_session(_today())
                return session, [{"role": "assistant", "content": welcome}]

            def respond(
                message: str,
                history: list[dict[str, str]],
                session: ConversationSession | None,
            ) -> tuple[str, list[dict[str, str]], ConversationSession]:
                today = _today()
                if session is None:
                    session, welcome = self._manager.start_session(today)
                    history = [*history, {"role": "assistant", "content": welcome}]
                sanitized = _sanitize_input(message, self._settings.input_max_chars)
                if not self._rate_limiter.allow(session):
                    response = "You're sending messages too quickly. Please wait a moment before trying again."
                else:
                    response, session = self._manager.handle_message(sanitized, session, today)
                history = [
                    *history,
                    {"role": "user", "content": message},
                    {"role": "assistant", "content": response},
                ]
                return "", history, session

            def reset() -> tuple[ConversationSession, list[dict[str, str]]]:
                session, welcome = self._manager.start_session(_today())
                return session, [{"role": "assistant", "content": welcome}]

            app.load(initialize, outputs=[session_state, chat_history])
            user_input.submit(
                respond,
                inputs=[user_input, chat_history, session_state],
                outputs=[user_input, chat_history, session_state],
            )
            reset_button.click(reset, outputs=[session_state, chat_history])

        return app


def _today() -> date:
    """Return today's date in UTC."""
    return datetime.now(tz=UTC).date()


def _sanitize_input(message: str, max_chars: int) -> str:
    """Normalize and truncate user input."""
    normalized = message.strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip()


@dataclass
class _RateLimiter:
    """Simple sliding-window rate limiter per session."""

    max_requests: int
    window_seconds: int
    _requests: dict[int, list[float]] = field(default_factory=dict)

    def allow(self, session: ConversationSession) -> bool:
        """Return whether the request is allowed for this session."""
        now = datetime.now(tz=UTC).timestamp()
        key = id(session)
        entries = [entry for entry in self._requests.get(key, []) if now - entry < self.window_seconds]
        if len(entries) >= self.max_requests:
            self._requests[key] = entries
            return False
        entries.append(now)
        self._requests[key] = entries
        return True
