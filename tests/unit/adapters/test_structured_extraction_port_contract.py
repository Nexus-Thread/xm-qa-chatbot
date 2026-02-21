"""Contract tests for StructuredExtractionPort adapter behavior."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from qa_chatbot.adapters.output.llm.structured_extraction import OpenAISettings, OpenAIStructuredExtractionAdapter
from qa_chatbot.adapters.output.llm.structured_extraction.prompts import SYSTEM_PROMPT, TEST_COVERAGE_PROMPT, TIME_WINDOW_PROMPT
from qa_chatbot.application.dtos import HistoryExtractionRequest
from qa_chatbot.domain import ProjectId, TimeWindow
from qa_chatbot.domain.registries import build_default_stream_project_registry

EXPECTED_MANUAL_TOTAL = 9
EXPECTED_AUTOMATED_TOTAL = 5
EXPECTED_SUPPORTED_RELEASES_COUNT = 3
EXPECTED_HISTORY_EXTRACTION_CALLS = 3


@dataclass
class _FakeMessage:
    """Fake message structure for completion responses."""

    content: str | None


@dataclass
class _FakeChoice:
    """Fake choice structure for completion responses."""

    message: _FakeMessage | None


@dataclass
class _FakeResponse:
    """Fake response returned by the transport client."""

    choices: list[_FakeChoice]


class _CapturingOpenAITransportClient:
    """Capture calls while returning pre-seeded completion responses."""

    def __init__(self, responses: list[_FakeResponse]) -> None:
        """Store fake responses and initialize capture state."""
        self._responses = iter(responses)
        self.calls: list[dict[str, Any]] = []

    def create_json_completion(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
    ) -> _FakeResponse:
        """Capture request payload and return the next fake response."""
        self.calls.append(
            {
                "model": model,
                "messages": messages,
            }
        )
        return next(self._responses)


def test_extract_project_id_contract_maps_response_and_builds_request_prompt() -> None:
    """Map project extraction response and include prompt plus conversation in request."""
    client = _CapturingOpenAITransportClient(
        [_FakeResponse([_FakeChoice(_FakeMessage('{"project_id": "Bridge", "confidence": "medium"}'))])]
    )
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    project_id, confidence = adapter.extract_project_id(
        "Bridge project status",
        build_default_stream_project_registry(),
    )

    assert project_id == ProjectId("bridge")
    assert confidence.value == "medium"
    assert len(client.calls) == 1

    request = client.calls[0]
    assert request["model"] == "llama2"
    assert request["messages"][0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert request["messages"][1]["role"] == "user"
    assert "Extract the project name from the conversation" in request["messages"][1]["content"]
    assert "Conversation:\nBridge project status" in request["messages"][1]["content"]


def test_extract_time_window_contract_maps_response_and_uses_time_window_prompt() -> None:
    """Map time window response and send the time-window extraction prompt."""
    client = _CapturingOpenAITransportClient([_FakeResponse([_FakeChoice(_FakeMessage('{"kind": "iso_month", "month": "2026-01"}'))])])
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    result = adapter.extract_time_window("January 2026", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 1)
    assert len(client.calls) == 1
    assert TIME_WINDOW_PROMPT in client.calls[0]["messages"][1]["content"]


def test_extract_coverage_contract_maps_payload_and_uses_coverage_prompt() -> None:
    """Map test coverage payload fields and send the coverage extraction prompt."""
    client = _CapturingOpenAITransportClient(
        [_FakeResponse([_FakeChoice(_FakeMessage('{"manual_total": 9, "automated_total": 5, "supported_releases_count": 3}'))])]
    )
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    result = adapter.extract_coverage("Manual total is nine and automated is five")

    assert result.metrics.manual_total == EXPECTED_MANUAL_TOTAL
    assert result.metrics.automated_total == EXPECTED_AUTOMATED_TOTAL
    assert result.supported_releases_count == EXPECTED_SUPPORTED_RELEASES_COUNT
    assert len(client.calls) == 1
    assert TEST_COVERAGE_PROMPT in client.calls[0]["messages"][1]["content"]


def test_extract_with_history_contract_uses_history_and_maps_selected_outputs() -> None:
    """Include normalized history in requests and map extracted project, month, and coverage."""
    client = _CapturingOpenAITransportClient(
        [
            _FakeResponse([_FakeChoice(_FakeMessage('{"project_id": "Bridge", "confidence": "high"}'))]),
            _FakeResponse([_FakeChoice(_FakeMessage('{"kind": "iso_month", "month": "2026-01"}'))]),
            _FakeResponse([_FakeChoice(_FakeMessage('{"manual_total": 9, "supported_releases_count": 3}'))]),
        ]
    )
    adapter = OpenAIStructuredExtractionAdapter(
        settings=OpenAISettings(base_url="http://localhost", api_key="test", model="llama2"),
        client=client,
    )

    result = adapter.extract_with_history(
        request=HistoryExtractionRequest(
            conversation="Bridge report for January",
            history=[
                {"role": " user ", "content": "  initial context  "},
                {"role": "assistant", "content": "previous summary"},
            ],
            include_project_id=True,
            include_time_window=True,
            include_test_coverage=True,
            include_supported_releases_count=True,
        ),
        current_date=date(2026, 2, 10),
        registry=build_default_stream_project_registry(),
    )

    assert result.project_id == ProjectId("bridge")
    assert result.time_window == TimeWindow.from_year_month(2026, 1)
    assert result.metrics.test_coverage is not None
    assert result.metrics.test_coverage.manual_total == EXPECTED_MANUAL_TOTAL
    assert result.metrics.supported_releases_count == EXPECTED_SUPPORTED_RELEASES_COUNT

    assert len(client.calls) == EXPECTED_HISTORY_EXTRACTION_CALLS

    first_call_messages = client.calls[0]["messages"]
    assert first_call_messages[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert first_call_messages[1] == {"role": "user", "content": "initial context"}
    assert first_call_messages[2] == {"role": "assistant", "content": "previous summary"}
    assert "Extract the project name from the conversation" in first_call_messages[3]["content"]
    assert TIME_WINDOW_PROMPT in client.calls[1]["messages"][3]["content"]
    assert TEST_COVERAGE_PROMPT in client.calls[2]["messages"][3]["content"]
