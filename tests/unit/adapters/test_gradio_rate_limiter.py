"""Unit tests for Gradio rate limiting utilities."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from qa_chatbot.adapters.input.gradio.adapter import _RateLimiter, _sanitize_input
from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationSession


def test_rate_limiter_allows_until_limit() -> None:
    """Allow requests until the limit is reached."""
    limiter = _RateLimiter(max_requests=2, window_seconds=60)
    session = ConversationSession()

    assert limiter.allow(session) is True
    assert limiter.allow(session) is True
    assert limiter.allow(session) is False


if TYPE_CHECKING:
    from _pytest.monkeypatch import MonkeyPatch


def test_rate_limiter_resets_after_window(monkeypatch: MonkeyPatch) -> None:
    """Allow requests again after the time window passes."""
    limiter = _RateLimiter(max_requests=1, window_seconds=10)
    session = ConversationSession()
    start = datetime(2026, 1, 1, tzinfo=UTC)

    def fake_now(_: object, tz: object | None = None) -> datetime:
        _ = tz
        return start

    def fake_now_later(_: object, tz: object | None = None) -> datetime:
        _ = tz
        return start.replace(second=start.second + 11)

    fake_datetime = type("Fake", (), {"now": classmethod(fake_now)})
    monkeypatch.setattr("qa_chatbot.adapters.input.gradio.adapter.datetime", fake_datetime)
    assert limiter.allow(session) is True

    fake_datetime_later = type("Fake", (), {"now": classmethod(fake_now_later)})
    monkeypatch.setattr("qa_chatbot.adapters.input.gradio.adapter.datetime", fake_datetime_later)
    assert limiter.allow(session) is True


def test_sanitize_input_trims_and_limits_length() -> None:
    """Trim whitespace and enforce max length."""
    message = "  hello world  "
    assert _sanitize_input(message, max_chars=20) == "hello world"
    assert _sanitize_input(message, max_chars=5) == "hello"
