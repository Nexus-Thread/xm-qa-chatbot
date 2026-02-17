"""Unit tests for OpenAI transport client utilities."""

from __future__ import annotations

import httpx
import pytest
from openai import APIError

from qa_chatbot.adapters.output.llm.openai import OpenAIClient, build_http_client

EXPECTED_TIMEOUT_SECONDS = 12.5
EXPECTED_CALLS_AFTER_RETRY_SUCCESS = 2
EXPECTED_CALLS_AFTER_RETRY_FAILURE = 3


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

    monkeypatch.setattr("qa_chatbot.adapters.output.llm.openai.factory.httpx.Client", fake_httpx_client)
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

    client.create_json_completion(model="llama2", messages=messages)

    assert sdk_client.chat.completions.last_call == {
        "model": "llama2",
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0,
    }


def test_openai_client_retries_on_api_error() -> None:
    """Retry transport call with exponential backoff on APIError."""
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    transient_error = APIError("temporary failure", request=request, body=None)
    sentinel_response = object()
    calls: list[object] = [transient_error, sentinel_response]
    sleep_calls: list[float] = []

    class FakeRetryCompletions:
        """Fake completions API that fails once then succeeds."""

        def __init__(self) -> None:
            """Track call count for retries."""
            self.calls = 0

        def create(self, **_: object) -> object:
            """Return next fake result for retry flow."""
            self.calls += 1
            result = calls[self.calls - 1]
            if isinstance(result, Exception):
                raise result
            return result

    class FakeRetryChat:
        """Fake chat namespace for retry test."""

        def __init__(self) -> None:
            """Attach retry completions."""
            self.completions = FakeRetryCompletions()

    class FakeRetrySDKClient:
        """Fake SDK client for retry test."""

        def __init__(self) -> None:
            """Attach chat namespace."""
            self.chat = FakeRetryChat()

    sdk_client = FakeRetrySDKClient()
    client = OpenAIClient(sdk_client=sdk_client, max_retries=3, backoff_seconds=0.5, sleep=sleep_calls.append)

    response = client.create_json_completion(model="llama2", messages=[{"role": "user", "content": "hello"}])

    assert response is sentinel_response
    assert sdk_client.chat.completions.calls == EXPECTED_CALLS_AFTER_RETRY_SUCCESS
    assert sleep_calls == [0.5]


def test_openai_client_raises_after_max_retries() -> None:
    """Raise APIError after exhausting retry attempts."""
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    transient_error = APIError("temporary failure", request=request, body=None)
    sleep_calls: list[float] = []

    class AlwaysFailCompletions:
        """Fake completions API that always raises APIError."""

        def __init__(self) -> None:
            """Track call count for retries."""
            self.calls = 0

        def create(self, **_: object) -> object:
            """Raise transient API error."""
            self.calls += 1
            raise transient_error

    class AlwaysFailChat:
        """Fake chat namespace with failing completions."""

        def __init__(self) -> None:
            """Attach failing completions API."""
            self.completions = AlwaysFailCompletions()

    class AlwaysFailSDKClient:
        """Fake SDK client that always fails."""

        def __init__(self) -> None:
            """Attach chat namespace."""
            self.chat = AlwaysFailChat()

    sdk_client = AlwaysFailSDKClient()
    client = OpenAIClient(sdk_client=sdk_client, max_retries=3, backoff_seconds=0.5, sleep=sleep_calls.append)

    with pytest.raises(APIError):
        client.create_json_completion(model="llama2", messages=[{"role": "user", "content": "hello"}])

    assert sdk_client.chat.completions.calls == EXPECTED_CALLS_AFTER_RETRY_FAILURE
    assert sleep_calls == [0.5, 1.0]
