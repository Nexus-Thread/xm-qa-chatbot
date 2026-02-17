"""Unit tests for OpenAI transport client utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

import httpx

from qa_chatbot.adapters.output.llm.openai.client import OpenAIClient, build_http_client

if TYPE_CHECKING:
    import pytest

EXPECTED_TIMEOUT_SECONDS = 12.5


class FakeCompletions:
    """Fake completions API for transport wrapper tests."""

    def __init__(self) -> None:
        """Initialize call tracking for completion requests."""
        self.last_call: dict[str, object] | None = None

    def create(self, **kwargs: object) -> object:
        """Store completion arguments and return a fake response."""
        self.last_call = kwargs
        return object()


class FakeChat:
    """Fake chat API for transport wrapper tests."""

    def __init__(self) -> None:
        """Attach fake completions API."""
        self.completions = FakeCompletions()


class FakeSDKClient:
    """Fake OpenAI SDK client for transport wrapper tests."""

    def __init__(self) -> None:
        """Attach fake chat namespace."""
        self.chat = FakeChat()


def test_build_http_client_applies_verify_and_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    """Build http client with explicit SSL verify and timeout settings."""
    captured_args: dict[str, object] = {}
    sentinel_client = object()

    def fake_httpx_client(*, verify: bool, timeout: httpx.Timeout) -> object:
        captured_args["verify"] = verify
        captured_args["timeout"] = timeout
        return sentinel_client

    monkeypatch.setattr("qa_chatbot.adapters.output.llm.openai.client.httpx.Client", fake_httpx_client)
    client = build_http_client(verify_ssl=False, timeout_seconds=EXPECTED_TIMEOUT_SECONDS)

    timeout = captured_args["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert captured_args["verify"] is False
    assert timeout.connect == EXPECTED_TIMEOUT_SECONDS
    assert timeout.read == EXPECTED_TIMEOUT_SECONDS
    assert timeout.write == EXPECTED_TIMEOUT_SECONDS
    assert timeout.pool == EXPECTED_TIMEOUT_SECONDS
    assert client is sentinel_client


def test_openai_client_creates_json_completion_with_expected_args() -> None:
    """Delegate completion call with JSON response format."""
    sdk_client = FakeSDKClient()
    client = OpenAIClient(sdk_client=sdk_client)
    messages = [{"role": "user", "content": "hello"}]

    client.create_json_completion(model="llama2", messages=messages, temperature=0.2)

    assert sdk_client.chat.completions.last_call == {
        "model": "llama2",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
    }
