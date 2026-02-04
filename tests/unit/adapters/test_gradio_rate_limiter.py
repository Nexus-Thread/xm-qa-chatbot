"""Unit tests for Gradio rate limiting utilities."""

from __future__ import annotations

from datetime import UTC, datetime

from qa_chatbot.adapters.input.gradio.adapter import _RateLimiter
from qa_chatbot.adapters.input.gradio.conversation_manager import ConversationSession


def test_rate_limiter_allows_until_limit() -> None:
    """Allow requests until the limit is reached."""
    limiter = _RateLimiter(max_requests=2, window_seconds=60)
    session = ConversationSession()

    assert limiter.allow(session) is True
    assert limiter.allow(session) is True
    assert limiter.allow(session) is False


def test_rate_limiter_resets_after_window(monkeypatch: object) -> None:
    """Allow requests again after the time window passes."""
    limiter = _RateLimiter(max_requests=1, window_seconds=10)
    session = ConversationSession()
    start = datetime(2026, 1, 1, tzinfo=UTC)

    def fake_now(_: object, tz: object = None) -> datetime:
        _ = tz
        return start

    def fake_now_later(_: object, tz: object = None) -> datetime:
        _ = tz
        return start.replace(second=start.second + 11)

    fake_datetime = type("Fake", (), {"now": classmethod(fake_now)})
    monkeypatch.setattr("qa_chatbot.adapters.input.gradio.adapter.datetime", fake_datetime)
    assert limiter.allow(session) is True

    fake_datetime_later = type("Fake", (), {"now": classmethod(fake_now_later)})
    monkeypatch.setattr("qa_chatbot.adapters.input.gradio.adapter.datetime", fake_datetime_later)
    assert limiter.allow(session) is True
