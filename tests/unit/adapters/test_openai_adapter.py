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
    OpenAISettings,
    OpenAIStructuredExtractionAdapter,
)
from qa_chatbot.application.dtos import HistoryExtractionRequest
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
EXPECTED_SINGLE_COVERAGE_CALLS = 1
EXPECTED_HISTORY_MANUAL_TOTAL = 7
EXPECTED_HISTORY_SUPPORTED_RELEASES = 2


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
    ) -> FakeResponse:
        """Create a fake JSON completion response."""
        _ = model, messages
        return self._completions.create()


def test_extract_project_id_parses_response() -> None:
    """Parse a project identifier from JSON response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Bridge", "confidence": "high"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
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
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    _, confidence = adapter.extract_project_id("We are Bridge", registry)

    assert confidence == ExtractionConfidence.low()


def test_extract_project_id_raises_on_unmatched_registry_project() -> None:
    """Raise when extracted project does not exist in registry."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "Unknown Team", "confidence": "low"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    with pytest.raises(AmbiguousExtractionError):
        adapter.extract_project_id("We are Unknown Team", registry)


def test_extract_time_window_parses_month() -> None:
    """Parse a YYYY-MM time window response."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "iso_month", "month": "2026-01"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_time_window("January 2026", date(2026, 2, 2))

    assert result == TimeWindow.from_year_month(2026, 1)


def test_extract_time_window_raises_on_invalid_format() -> None:
    """Raise when time window format is invalid."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "iso_month", "month": "Jan"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("Jan", date(2026, 2, 2))


def test_extract_time_window_supports_current_keyword() -> None:
    """Resolve current month keyword into a TimeWindow."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "current_month", "month": null}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_time_window("current", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 2)


def test_extract_time_window_supports_previous_month_kind() -> None:
    """Resolve previous month kind into a TimeWindow."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "previous_month", "month": null}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_time_window("previous month", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 1)


def test_extract_time_window_raises_when_iso_month_has_null_month() -> None:
    """Raise when iso_month kind is returned without month."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "iso_month", "month": null}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_when_current_month_has_non_null_month() -> None:
    """Raise when current_month kind provides a non-null month."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "current_month", "month": "2026-02"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("current month", date(2026, 2, 2))


def test_extract_time_window_raises_on_legacy_month_only_shape() -> None:
    """Raise when legacy month-only payload is returned."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"month": "2026-01"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_project_id_raises_for_blank_response() -> None:
    """Raise when project id is missing."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"project_id": "", "confidence": "low"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    registry = build_default_stream_project_registry()
    with pytest.raises(AmbiguousExtractionError):
        adapter.extract_project_id("Unknown", registry)


def test_extract_coverage_accepts_partial_data() -> None:
    """Accept partial coverage data with null fields."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": null}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_coverage("Manual total is 100")

    assert result.metrics.manual_total == EXPECTED_MANUAL_TOTAL
    assert result.metrics.automated_total is None
    assert result.metrics.manual_created_in_reporting_month is None
    assert result.supported_releases_count is None


def test_extract_coverage_accepts_all_null() -> None:
    """Accept response with all null fields."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": null}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    result = adapter.extract_coverage("No metrics provided")

    assert result.metrics.manual_total is None
    assert result.metrics.automated_total is None
    assert result.supported_releases_count is None


def test_extract_coverage_raises_on_negative_manual_total() -> None:
    """Raise when coverage payload contains a negative count."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": -1}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_coverage("Manual total is -1")


def test_extract_supported_releases_raises_on_negative_value() -> None:
    """Raise when supported releases count is negative."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"supported_releases_count": -1}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_coverage("Supported releases are -1")


def test_extract_time_window_raises_when_response_has_no_choices() -> None:
    """Raise when provider response has no choices."""
    responses = iter([FakeResponse(choices=[])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_when_message_is_missing() -> None:
    """Raise when provider choice does not include a message."""
    responses = iter([FakeResponse([FakeChoice(message=None)])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_on_invalid_json() -> None:
    """Raise when the model response is not valid JSON."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage("not-json"))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_time_window_raises_when_message_content_is_missing() -> None:
    """Raise when provider message content is missing."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage(content=None))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(responses),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_time_window("January 2026", date(2026, 2, 2))


def test_extract_coverage_performs_single_extraction_call_for_metrics_and_releases() -> None:
    """Use one API call to extract both coverage metrics and supported releases."""
    responses = iter(
        [FakeResponse([FakeChoice(FakeMessage('{"manual_total": 100, "automated_total": 20, "supported_releases_count": 4}'))])]
    )
    client = FakeOpenAITransportClient(responses)
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    coverage = adapter.extract_coverage("Coverage update")

    assert coverage.metrics.manual_total == EXPECTED_MANUAL_TOTAL
    assert coverage.supported_releases_count == EXPECTED_SUPPORTED_RELEASES_COUNT
    assert client.calls == EXPECTED_SINGLE_COVERAGE_CALLS


def test_extract_with_history_skips_project_extraction_when_known() -> None:
    """Skip project extraction call when known project is provided and extraction is disabled."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"kind": "iso_month", "month": "2026-01"}'))])])
    client = FakeOpenAITransportClient(responses)
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    result = adapter.extract_with_history(
        request=HistoryExtractionRequest(
            conversation="Conversation",
            history=[{"role": "user", "content": "hello"}],
            known_project_id=ProjectId("bridge"),
            known_supported_releases_count=EXPECTED_HISTORY_SUPPORTED_RELEASES,
            include_project_id=False,
            include_test_coverage=False,
            include_supported_releases_count=True,
        ),
        current_date=date(2026, 2, 2),
        registry=build_default_stream_project_registry(),
    )

    assert result.project_id == ProjectId("bridge")
    assert result.time_window == TimeWindow.from_year_month(2026, 1)
    assert client.calls == 1


def test_extract_with_history_extracts_coverage_once_for_metrics_and_releases() -> None:
    """Extract coverage and supported releases with a single API call."""
    responses = iter([FakeResponse([FakeChoice(FakeMessage('{"manual_total": 7, "supported_releases_count": 2}'))])])
    client = FakeOpenAITransportClient(responses)
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    result = adapter.extract_with_history(
        request=HistoryExtractionRequest(
            conversation="Conversation",
            history=[{"role": "user", "content": "hello"}],
            known_project_id=ProjectId("bridge"),
            known_time_window=TimeWindow.from_year_month(2026, 1),
            include_project_id=False,
            include_time_window=False,
            include_test_coverage=True,
            include_supported_releases_count=True,
        ),
        current_date=date(2026, 2, 2),
        registry=build_default_stream_project_registry(),
    )

    assert result.metrics.test_coverage is not None
    assert result.metrics.test_coverage.manual_total == EXPECTED_HISTORY_MANUAL_TOTAL
    assert result.metrics.supported_releases_count == EXPECTED_HISTORY_SUPPORTED_RELEASES
    assert client.calls == 1


def test_extract_with_history_raises_when_required_known_project_missing() -> None:
    """Raise when project extraction is disabled and known project is not provided."""
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(iter(())),
    )

    with pytest.raises(LLMExtractionError):
        adapter.extract_with_history(
            request=HistoryExtractionRequest(
                conversation="Conversation",
                history=None,
                include_project_id=False,
            ),
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )


def test_extract_time_window_raises_extraction_error_on_api_error() -> None:
    """Translate APIError from transport client into LLMExtractionError."""
    request = httpx.Request("POST", "https://example.com/v1/chat/completions")
    responses: Iterator[FakeResponse | Exception] = iter(
        [
            APIError("temporary failure", request=request, body=None),
        ]
    )
    adapter = OpenAIStructuredExtractionAdapter(
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
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(empty_responses),
    )

    with pytest.raises(InvalidHistoryError):
        adapter.extract_with_history(
            request=HistoryExtractionRequest(
                conversation="Conversation",
                history=[{"role": "bot", "content": "Hello"}],
            ),
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )


def test_extract_with_history_raises_on_blank_content() -> None:
    """Raise when history contains blank content."""
    empty_responses: Iterator[FakeResponse | Exception] = iter(())
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(empty_responses),
    )

    with pytest.raises(InvalidHistoryError):
        adapter.extract_with_history(
            request=HistoryExtractionRequest(
                conversation="Conversation",
                history=[{"role": "user", "content": "   "}],
            ),
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )


def test_extract_with_history_raises_when_required_known_time_window_missing() -> None:
    """Raise when time-window extraction is disabled and known time window is missing."""
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=FakeOpenAITransportClient(iter(())),
    )

    with pytest.raises(LLMExtractionError, match="Time window is required for history extraction"):
        adapter.extract_with_history(
            request=HistoryExtractionRequest(
                conversation="Conversation",
                history=None,
                known_project_id=ProjectId("bridge"),
                include_project_id=False,
                include_time_window=False,
            ),
            current_date=date(2026, 2, 2),
            registry=build_default_stream_project_registry(),
        )
