"""Unit tests for structured extraction helper modules."""

from __future__ import annotations

from datetime import date

import pytest

from qa_chatbot.adapters.output.llm.structured_extraction.exceptions import (
    InvalidHistoryError,
    LLMExtractionError,
)
from qa_chatbot.adapters.output.llm.structured_extraction.history import normalize_history
from qa_chatbot.adapters.output.llm.structured_extraction.mappers import to_test_coverage_metrics
from qa_chatbot.adapters.output.llm.structured_extraction.parsers import resolve_time_window
from qa_chatbot.adapters.output.llm.structured_extraction.schemas import TestCoverageSchema as CoverageSchema
from qa_chatbot.domain import TimeWindow

EXPECTED_MANUAL_TOTAL = 10
EXPECTED_AUTOMATED_TOTAL = 12
EXPECTED_MANUAL_CREATED = 1
EXPECTED_MANUAL_UPDATED = 2
EXPECTED_AUTOMATED_CREATED = 3
EXPECTED_AUTOMATED_UPDATED = 4
EXPECTED_SUPPORTED_RELEASES_COUNT = 5


def test_normalize_history_returns_empty_for_none() -> None:
    """Return empty history when no input history is provided."""
    assert normalize_history(None) == []


def test_normalize_history_strips_valid_entries() -> None:
    """Normalize valid history role and content values."""
    result = normalize_history(
        [
            {
                "role": " user ",
                "content": "  hello  ",
            }
        ]
    )

    assert result == [{"role": "user", "content": "hello"}]


def test_normalize_history_raises_for_invalid_role() -> None:
    """Raise when history role is not in allowed role set."""
    with pytest.raises(InvalidHistoryError):
        normalize_history([{"role": "bot", "content": "hello"}])


def test_resolve_time_window_resolves_previous_keyword() -> None:
    """Resolve previous month keyword into default previous reporting month."""
    result = resolve_time_window("previous", date(2026, 2, 10))

    assert result == TimeWindow.from_year_month(2026, 1)


def test_resolve_time_window_raises_for_invalid_value() -> None:
    """Raise when time window value does not match supported formats."""
    with pytest.raises(LLMExtractionError):
        resolve_time_window("January", date(2026, 2, 10))


def test_to_test_coverage_metrics_maps_schema_fields() -> None:
    """Map schema fields directly to test coverage domain metrics."""
    payload = CoverageSchema(
        manual_total=EXPECTED_MANUAL_TOTAL,
        automated_total=EXPECTED_AUTOMATED_TOTAL,
        manual_created_in_reporting_month=EXPECTED_MANUAL_CREATED,
        manual_updated_in_reporting_month=EXPECTED_MANUAL_UPDATED,
        automated_created_in_reporting_month=EXPECTED_AUTOMATED_CREATED,
        automated_updated_in_reporting_month=EXPECTED_AUTOMATED_UPDATED,
        supported_releases_count=EXPECTED_SUPPORTED_RELEASES_COUNT,
    )

    result = to_test_coverage_metrics(payload)

    assert result.manual_total == EXPECTED_MANUAL_TOTAL
    assert result.automated_total == EXPECTED_AUTOMATED_TOTAL
    assert result.manual_created_in_reporting_month == EXPECTED_MANUAL_CREATED
    assert result.manual_updated_in_reporting_month == EXPECTED_MANUAL_UPDATED
    assert result.automated_created_in_reporting_month == EXPECTED_AUTOMATED_CREATED
    assert result.automated_updated_in_reporting_month == EXPECTED_AUTOMATED_UPDATED
    assert result.percentage_automation is None
