"""Unit tests for OpenAI adapter parsing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING

import httpx
import pytest
from openai import APIError

from qa_chatbot.adapters.output.llm.structured_extraction import (
    AmbiguousExtractionError,
    InvalidHistoryError,
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
EXPECTED_SUPPORTED_RELEASES_COUNT = 4
EXPECTED_INDEPENDENT_COVERAGE_CALLS = 2


@dataclass
class FakeMessage:
    """Fake message structure for OpenAI responses."""

    content: str | None


@dataclass
class FakeChoice:
    """Fake choice structure for OpenAI responses."""

    message: FakeMessage | None


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

    def __init__(self, responses: Iterator[FakeResponse | Exception]) -> None:
        """Store the iterator of fake responses."""
        self._responses = responses
        self.calls = 0

    def create(self, **_: object) -> FakeResponse:
        """Return the next fake response."""
        self.calls += 1
        result = next(self._responses)
        if isinstance(result, Exception):
            raise result
        return result


class FakeOpenAITransportClient:
    """Fake transport client matching the OpenAI client protocol."""

    def __init__(self, responses: Iterator[FakeResponse | Exception]) -> None:
        """Store fake completion responses."""
        self._completions = FakeCompletions(responses)

    @property
    def calls(self) -> int:
        """Return how many completion calls were made."""
        return self._completions.calls

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0,
    ) -> FakeResponse:
        """Create a fake JSON completion response."""
        _ = model, messages, temperature
        return self._completions.create()


def test_extract_project_id_parses_response() -> None:
    """Parse a project identifier from JSON response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Bridge", "confidence": "high"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    project_id, confidence = adapter.extract_project_id("We are Bridge", registry)

    assert project_id == ProjectId("bridge")
    assert confidence == ExtractionConfidence.from_raw("high")


def test_extract_project_id_falls_back_to_low_on_invalid_confidence() -> None:
    """Fallback to low confidence when the model returns unsupported value."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Bridge", "confidence": "very sure"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    _, confidence = adapter.extract_project_id("We are Bridge", registry)

    assert confidence == ExtractionConfidence.low()


def test_extract_project_id_raises_on_unmatched_registry_project() -> None:
    """Raise when extracted project does not exist in registry."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Unknown Team", "confidence": "low"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    with pytest.raises(AmbiguousExtractionError):
        adapter.extract_project_id("We are Unknown Team", registry)


def test_extract_time_window_parses_month() -> None:
    """Parse a YYYY-MM time window response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "2026-01"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_time_window("January 2026", date(2026, 2, 2))

    assert result == TimeWindow.from_year_month(2026, 1)


def test_extract_time_window_raises_on_invalid_format() -> None:
    """Raise when time window format is invalid."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "Jan"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("Jan", date(2026, 2, 2))


def test_extract_time_window_supports_current_keyword() -> None:
    """Resolve current month keyword into a TimeWindow."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "current"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_time_window("current", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 2)


def test_extract_project_id_raises_for_blank_response() -> None:
    """Raise when project id is missing."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "", "confidence": "low"}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    with pytest.raises(AmbiguousExtractionError):
        adapter.extract_project_id("Unknown", registry)


def test_extract_test_coverage_accepts_partial_data() -> None:
    """Accept partial coverage data with null fields."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": null}'))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
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
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_test_coverage("No metrics provided")

    assert result.manual_total is None
    assert result.automated_total is None


def test_extract_time_window_raises_when_response_has_no_choices() -> None:
    """Raise when provider response has no choices."""
    responses = iter([FakeResponse(choices=[])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_when_message_is_missing() -> None:
    """Raise when provider choice does not include a message."""
    responses = iter([FakeResponse([FakeChoice(message=None)])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_on_invalid_json() -> None:
    """Raise when the model response is not valid JSON."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage("not-json"))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_when_message_content_is_missing() -> None:
    """Raise when provider message content is missing."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage(content=None))])])
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_supported_releases_performs_independent_extraction_calls() -> None:
    """Perform independent API calls for repeated coverage prompt extraction."""
    responses = iter(
        [
            FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": 20, "supported_releases_count": 4}'))]),
            FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": 20, "supported_releases_count": 4}'))]),
        ]
    )
    client = FakeOpenAITransportClient(responses)
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    coverage = adapter.extract_test_coverage("Coverage update")
    supported_releases = adapter.extract_supported_releases_count("Coverage update")

    assert coverage.manual_total == EXPECTED_MANUAL_TOTAL
    assert supported_releases == EXPECTED_SUPPORTED_RELEASES_COUNT
    assert client.calls == EXPECTED_INDEPENDENT_COVERAGE_CALLS


def test_extract_time_window_raises_extraction_error_on_api_error() -> None:
    """Translate APIError from transport client into LLMExtractionError."""
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    responses: Iterator[FakeResponse | Exception] = iter(
        [
            APIError("temporary failure", request=request, body=None),
        ]
    )
    adapter = OpenAIAdapter(
        settings=OpenAISettings(
            base_url="http://localhost",
            api_key="test",
            model="llama2",
        ),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_with_history_raises_on_invalid_role() -> None:
    """Raise when history contains an invalid role."""
    empty_responses: Iterator[FakeResponse | Exception] = iter(())
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(empty_responses),
    )

    with pytest.raises(InvalidHistoryError):
        adapter.extract_with_history(
            conversation="Conversation",
            history=[{"role": "bot", "content": "Hello"}],
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )


def test_extract_with_history_raises_on_blank_content() -> None:
    """Raise when history contains blank content."""
    empty_responses: Iterator[FakeResponse | Exception] = iter(())
    adapter = OpenAIAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(empty_responses),
    )

    with pytest.raises(InvalidHistoryError):
        adapter.extract_with_history(
            conversation="Conversation",
            history=[{"role": "user", "content": "   "}],
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )
