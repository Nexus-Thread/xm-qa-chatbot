"""Unit tests for Gradio adapter wiring and callbacks."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import TYPE_CHECKING, Literal, Self, cast

import qa_chatbot.adapters.input.gradio.adapter as gradio_adapter_module
from qa_chatbot.adapters.input.gradio import ConversationSession, GradioAdapter, GradioSettings

if TYPE_CHECKING:
    from collections.abc import Callable
    from datetime import date

    from _pytest.monkeypatch import MonkeyPatch

    from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationManager

RATE_LIMITED_MESSAGE = "You're sending messages too quickly. Please wait a moment before trying again."


@dataclass
class _FakeConversationManager:
    """Fake conversation manager for Gradio callback tests."""

    start_calls: int = 0
    handled_messages: list[str] = field(default_factory=list)

    def start_session(self, current_date: date) -> tuple[ConversationSession, str]:
        """Return a deterministic session and welcome message."""
        _ = current_date
        self.start_calls += 1
        return ConversationSession(), "Welcome"

    def handle_message(
        self,
        message: str,
        session: ConversationSession,
        current_date: date,
    ) -> tuple[str, ConversationSession]:
        """Record handled messages and return a deterministic response."""
        _ = current_date
        self.handled_messages.append(message)
        return f"handled:{message}", session


@dataclass
class _FakeTextbox:
    """Fake Gradio textbox that captures submit callback registration."""

    submit_handler: Callable[..., tuple[str, list[dict[str, str]], ConversationSession]] | None = None

    def submit(self, fn: Callable[..., tuple[str, list[dict[str, str]], ConversationSession]], **_: object) -> None:
        """Capture submit callback."""
        self.submit_handler = fn


@dataclass
class _FakeButton:
    """Fake Gradio button that captures click callback registration."""

    click_handler: Callable[..., tuple[ConversationSession, list[dict[str, str]]]] | None = None

    def click(self, fn: Callable[..., tuple[ConversationSession, list[dict[str, str]]]], **_: object) -> None:
        """Capture click callback."""
        self.click_handler = fn


@dataclass
class _FakeBlocks:
    """Fake Gradio blocks context that captures app-level callbacks."""

    load_handler: Callable[..., tuple[ConversationSession, list[dict[str, str]]]] | None = None
    launch_kwargs: dict[str, object] | None = None

    def __enter__(self) -> Self:
        """Enter context manager."""
        return self

    def __exit__(self, *_: object) -> Literal[False]:
        """Exit context manager without suppressing exceptions."""
        return False

    def load(self, fn: Callable[..., tuple[ConversationSession, list[dict[str, str]]]], **_: object) -> None:
        """Capture load callback."""
        self.load_handler = fn

    def launch(self, **kwargs: object) -> None:
        """Capture launch configuration."""
        self.launch_kwargs = kwargs


@dataclass
class _FakeGradioHarness:
    """Collected fake Gradio components for assertions."""

    app: _FakeBlocks | None = None
    textbox: _FakeTextbox | None = None
    button: _FakeButton | None = None


def _patch_gradio(monkeypatch: MonkeyPatch) -> _FakeGradioHarness:
    """Replace the gradio module with lightweight test doubles."""
    harness = _FakeGradioHarness()

    def _noop(*_: object, **__: object) -> None:
        return None

    def _object_factory(*_: object, **__: object) -> object:
        return object()

    def blocks_factory() -> _FakeBlocks:
        harness.app = _FakeBlocks()
        return harness.app

    def textbox_factory(**_: object) -> _FakeTextbox:
        harness.textbox = _FakeTextbox()
        return harness.textbox

    def button_factory(*_: object, **__: object) -> _FakeButton:
        harness.button = _FakeButton()
        return harness.button

    fake_gradio = SimpleNamespace(
        Blocks=blocks_factory,
        Markdown=_noop,
        State=_object_factory,
        Chatbot=_object_factory,
        Textbox=textbox_factory,
        Button=button_factory,
    )
    monkeypatch.setattr(gradio_adapter_module, "gradio", fake_gradio)
    return harness


def test_launch_uses_configured_server_options(monkeypatch: MonkeyPatch) -> None:
    """Launch should pass configured server options to Gradio."""
    manager = _FakeConversationManager()
    adapter = GradioAdapter(
        manager=cast("ConversationManager", manager),
        settings=GradioSettings(server_port=9911, share=True),
    )
    fake_app = _FakeBlocks()
    monkeypatch.setattr(adapter, "_build_ui", lambda: fake_app)

    adapter.launch()

    assert fake_app.launch_kwargs == {
        "server_port": 9911,
        "share": True,
        "show_error": True,
    }


def test_build_ui_registers_callbacks_and_processes_messages(monkeypatch: MonkeyPatch) -> None:
    """Launch should wire callbacks for initialize, submit, and reset paths."""
    harness = _patch_gradio(monkeypatch)
    manager = _FakeConversationManager()
    adapter = GradioAdapter(
        manager=cast("ConversationManager", manager),
        settings=GradioSettings(input_max_chars=5),
    )

    adapter.launch()

    assert harness.app is not None
    assert harness.app.load_handler is not None
    assert harness.textbox is not None
    assert harness.textbox.submit_handler is not None
    assert harness.button is not None
    assert harness.button.click_handler is not None

    initialized_session, initialized_history = harness.app.load_handler()
    assert initialized_session.state.name == "PROJECT_ID"
    assert initialized_history == [{"role": "assistant", "content": "Welcome"}]

    monkeypatch.setattr(gradio_adapter_module.RateLimiter, "allow", lambda *_: False)
    _, blocked_history, blocked_session = harness.textbox.submit_handler("  hello world  ", [], None)
    assert blocked_session is not None
    assert manager.handled_messages == []
    assert blocked_history[-1] == {"role": "assistant", "content": RATE_LIMITED_MESSAGE}

    monkeypatch.setattr(gradio_adapter_module.RateLimiter, "allow", lambda *_: True)
    _, allowed_history, _ = harness.textbox.submit_handler(
        "  hello world  ",
        [],
        ConversationSession(),
    )
    assert manager.handled_messages == ["hello"]
    assert allowed_history[-1] == {"role": "assistant", "content": "handled:hello"}

    reset_session, reset_history = harness.button.click_handler()
    assert reset_session.state.name == "PROJECT_ID"
    assert reset_history == [{"role": "assistant", "content": "Welcome"}]
