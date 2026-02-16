"""Unit tests for OpenAI adapter parsing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.output.llm.openai import (
    AmbiguousExtractionError,
    LLMExtractionError,
    OpenAIAdapter,
    OpenAISettings,
)
from qa_chatbot.domain import (
    ExtractionConfidence,
    ProjectId,
    TimeWindow,
)
from qa_chatbot.domain.registries import build_default_stream_project_registry

if TYPE_CHECKING:
    from collections.abc import Iterator

EXPECTED_MANUAL_TOTAL = 100


@dataclass
class FakeMessage:
    """Fake message structure for OpenAI responses."""

    content: str | None


@dataclass
class FakeChoice:
    """Fake choice structure for OpenAI responses."""

    message: FakeMessage


@dataclass
class FakeUsage:
    """Fake usage metadata for OpenAI responses."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class FakeResponse:
    """Fake response returned by the OpenAI client."""

    choices: list[FakeChoice]
    usage: FakeUsage | None = None


class FakeCompletions:
    """Fake completions client."""

    def __init__(self, responses: Iterator[FakeResponse]) -> None:
        """Store the iterator of fake responses."""
        self._responses = responses

    def create(self, **_: object) -> FakeResponse:
        """Return the next fake response."""
        return next(self._responses)


class FakeChat:
    """Fake chat client."""

    def __init__(self, responses: Iterator[FakeResponse]) -> None:
        """Attach fake completion responses."""
        self.completions = FakeCompletions(responses)


class FakeClient:
    """Fake OpenAI client."""

    def __init__(self, responses: Iterator[FakeResponse]) -> None:
        """Attach fake chat responses."""
        self.chat = FakeChat(responses)


def test_extract_project_id_parses_response() -> None:
    """Parse a project identifier from JSON response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Project A", "confidence": "high"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    registry = build_default_stream_project_registry()
    project_id, confidence = adapter.extract_project_id("We are Project A", registry)

    assert project_id == ProjectId("Project A")
    assert confidence == ExtractionConfidence.from_raw("high")


def test_extract_project_id_falls_back_to_low_on_invalid_confidence() -> None:
    """Fallback to low confidence when the model returns unsupported value."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Project A", "confidence": "very sure"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    registry = build_default_stream_project_registry()
    _, confidence = adapter.extract_project_id("We are Project A", registry)

    assert confidence == ExtractionConfidence.low()


def test_extract_time_window_parses_month() -> None:
    """Parse a YYYY-MM time window response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "2026-01"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    result = adapter.extract_time_window("January 2026", date(2026, 2, 2))

    assert result == TimeWindow.from_year_month(2026, 1)


def test_extract_time_window_raises_on_invalid_format() -> None:
    """Raise when time window format is invalid."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "Jan"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("Jan", date(2026, 2, 2))


def test_extract_time_window_supports_current_keyword() -> None:
    """Resolve current month keyword into a TimeWindow."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "current"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    result = adapter.extract_time_window("current", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 2)


def test_extract_project_id_raises_for_blank_response() -> None:
    """Raise when project id is missing."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "", "confidence": "low"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    registry = build_default_stream_project_registry()
    with pytest.raises(AmbiguousExtractionError):
        adapter.extract_project_id("Unknown", registry)


def test_extract_test_coverage_accepts_partial_data() -> None:
    """Accept partial coverage data with null fields."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": null}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    result = adapter.extract_test_coverage("Manual total is 100")

    assert result.manual_total == EXPECTED_MANUAL_TOTAL
    assert result.automated_total is None
    assert result.manual_created_in_reporting_month is None


def test_extract_test_coverage_accepts_all_null() -> None:
    """Accept response with all null fields."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": null}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeClient(responses),
    )

    result = adapter.extract_test_coverage("No metrics provided")

    assert result.manual_total is None
    assert result.automated_total is None
