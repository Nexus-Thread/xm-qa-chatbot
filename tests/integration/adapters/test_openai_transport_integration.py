"""Integration tests for OpenAI transport behavior with local fakes."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from qa_chatbot.adapters.output.llm.openai import OpenAIClient, extract_message_content

pytestmark = pytest.mark.integration


@dataclass
class _FakeMessage:
    content: str


@dataclass
class _FakeChoice:
    message: _FakeMessage


@dataclass
class _FakeResponse:
    choices: list[_FakeChoice]


class _FakeCompletions:
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **_: object) -> _FakeResponse:
        self.calls += 1
        return _FakeResponse(choices=[_FakeChoice(message=_FakeMessage(content='{"message":"hello world"}'))])


class _FakeChat:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()


class _FakeSDKClient:
    def __init__(self) -> None:
        self.chat = _FakeChat()


def test_openai_transport_returns_extractable_json_payload() -> None:
    """Return a response object compatible with shared response extractors."""
    transport = OpenAIClient(sdk_client=_FakeSDKClient())

    response = transport.create_json_completion(
        model="fake-model",
        messages=[{"role": "user", "content": "hello"}],
    )
    content = extract_message_content(response)

    assert content == '{"message":"hello world"}'
