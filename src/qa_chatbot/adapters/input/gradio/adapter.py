"""Gradio adapter for chat-based data collection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

import gradio as gr

from .conversation_manager import ConversationManager, ConversationSession  # noqa: TC001


@dataclass(frozen=True)
class GradioSettings:
    """Settings for configuring the Gradio server."""

    server_port: int = 7860
    share: bool = False


class GradioAdapter:
    """Gradio UI adapter for the QA chatbot."""

    def __init__(self, manager: ConversationManager, settings: GradioSettings | None = None) -> None:
        """Initialize the Gradio adapter."""
        self._manager = manager
        self._settings = settings or GradioSettings()

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
                response, session = self._manager.handle_message(message, session, today)
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
