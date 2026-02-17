"""Unit tests for OpenAI response parsing helpers."""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from qa_chatbot.adapters.output.llm.openai import (
    OpenAIResponseError,
    extract_message_content,
    extract_usage,
)

EXPECTED_PROMPT_TOKENS = 12
EXPECTED_COMPLETION_TOKENS = 8
EXPECTED_TOTAL_TOKENS = 20


@dataclass
class FakeMessage:
    """Fake OpenAI message container."""

    content: str | None


@dataclass
class FakeChoice:
    """Fake OpenAI choice container."""

    message: FakeMessage | None


@dataclass
class FakeUsage:
    """Fake OpenAI usage container."""

    prompt_tokens: int | None
    completion_tokens: int | None
    total_tokens: int | None


@dataclass
class FakeResponse:
    """Fake OpenAI response container."""

    choices: list[FakeChoice] | None
    usage: FakeUsage | None = None


def test_extract_message_content_returns_first_choice_content() -> None:
    """Return content from first choice message."""
    response = FakeResponse(choices=[FakeChoice(FakeMessage(content='{"month": "2026-01"}'))])

    content = extract_message_content(response)

    assert content == '{"month": "2026-01"}'


def test_extract_message_content_raises_when_choices_are_missing() -> None:
    """Raise when response does not include choices."""
    response = FakeResponse(choices=[])

    with pytest.raises(OpenAIResponseError):
        extract_message_content(response)


def test_extract_message_content_raises_when_message_is_missing() -> None:
    """Raise when first choice does not include a message."""
    response = FakeResponse(choices=[FakeChoice(message=None)])

    with pytest.raises(OpenAIResponseError):
        extract_message_content(response)


def test_extract_message_content_raises_when_content_is_missing() -> None:
    """Raise when message does not include content."""
    response = FakeResponse(choices=[FakeChoice(FakeMessage(content=None))])

    with pytest.raises(OpenAIResponseError):
        extract_message_content(response)


def test_extract_usage_returns_none_without_usage() -> None:
    """Return None when usage metadata is absent."""
    response = FakeResponse(choices=[FakeChoice(FakeMessage(content="{}"))], usage=None)

    usage = extract_usage(response)

    assert usage is None


def test_extract_usage_maps_usage_fields() -> None:
    """Map usage metadata into a typed usage object."""
    response = FakeResponse(
        choices=[FakeChoice(FakeMessage(content="{}"))],
        usage=FakeUsage(
            prompt_tokens=EXPECTED_PROMPT_TOKENS,
            completion_tokens=EXPECTED_COMPLETION_TOKENS,
            total_tokens=EXPECTED_TOTAL_TOKENS,
        ),
    )

    usage = extract_usage(response)

    assert usage is not None
    assert usage.prompt_tokens == EXPECTED_PROMPT_TOKENS
    assert usage.completion_tokens == EXPECTED_COMPLETION_TOKENS
    assert usage.total_tokens == EXPECTED_TOTAL_TOKENS
