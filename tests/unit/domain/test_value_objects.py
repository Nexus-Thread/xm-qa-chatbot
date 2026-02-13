"""Unit tests for domain value objects."""

from datetime import date

import pytest

from qa_chatbot.domain import (
    ExtractionConfidence,
    InvalidConfigurationError,
    InvalidProjectIdError,
    InvalidStreamIdError,
    InvalidTimeWindowError,
    ProjectId,
    StreamId,
    TestCoverageMetrics,
    TimeWindow,
)

# Merge test constants
EXISTING_MANUAL_TOTAL = 1000
EXISTING_AUTOMATED_TOTAL = 500
EXISTING_MANUAL_CREATED = 10
EXISTING_MANUAL_UPDATED = 20
EXISTING_AUTOMATED_CREATED = 5
EXISTING_AUTOMATED_UPDATED = 3
EXISTING_PERCENTAGE = 33.33
UPDATED_MANUAL_TOTAL = 1100
PARTIAL_MANUAL_TOTAL = 100


def test_project_id_normalizes_value() -> None:
    """Normalize project identifiers."""
    project_id = ProjectId.from_raw("  Alpha ")

    assert project_id.value == "Alpha"


def test_project_id_rejects_empty_value() -> None:
    """Reject empty project identifiers."""
    with pytest.raises(InvalidProjectIdError):
        ProjectId.from_raw("  ")


def test_stream_id_normalizes_value() -> None:
    """Normalize stream identifiers."""
    stream_id = StreamId.from_raw("  backbone_platform ")

    assert stream_id.value == "backbone_platform"


def test_stream_id_rejects_empty_value() -> None:
    """Reject empty stream identifiers."""
    with pytest.raises(InvalidStreamIdError):
        StreamId.from_raw("  ")


def test_extraction_confidence_normalizes_value() -> None:
    """Normalize extraction confidence values."""
    confidence = ExtractionConfidence.from_raw("  HIGH  ")

    assert confidence.value == "high"
    assert confidence.is_high is True
    assert confidence.is_medium is False
    assert confidence.is_low is False


def test_extraction_confidence_named_constructors_are_symmetric() -> None:
    """Create confidence values via named constructors."""
    high = ExtractionConfidence.high()
    medium = ExtractionConfidence.medium()
    low = ExtractionConfidence.low()

    assert high.value == "high"
    assert high.is_high is True
    assert medium.value == "medium"
    assert medium.is_medium is True
    assert low.value == "low"
    assert low.is_low is True


def test_extraction_confidence_rejects_invalid_value() -> None:
    """Reject unsupported extraction confidence values."""
    with pytest.raises(InvalidConfigurationError, match="Confidence must be one of: high, medium, low"):
        ExtractionConfidence.from_raw("certain")


def test_time_window_validates_ranges() -> None:
    """Validate time window ranges."""
    with pytest.raises(InvalidTimeWindowError):
        TimeWindow.from_year_month(year=1999, month=1)

    with pytest.raises(InvalidTimeWindowError):
        TimeWindow.from_year_month(year=2024, month=13)


def test_time_window_default_uses_previous_month_within_grace() -> None:
    """Use previous month within grace period."""
    window = TimeWindow.default_for(date(2026, 2, 1), grace_period_days=2)

    assert window.to_iso_month() == "2026-01"


def test_time_window_default_uses_current_month_after_grace() -> None:
    """Use current month after grace period."""
    window = TimeWindow.default_for(date(2026, 2, 3), grace_period_days=2)

    assert window.to_iso_month() == "2026-02"


def test_test_coverage_rejects_negative_counts() -> None:
    """Reject invalid coverage metrics values."""
    with pytest.raises(ValueError, match="Test coverage counts must be non-negative"):
        TestCoverageMetrics(
            manual_total=-1,
            automated_total=0,
            manual_created_last_month=0,
            manual_updated_last_month=0,
            automated_created_last_month=0,
            automated_updated_last_month=0,
            percentage_automation=0.0,
        )


def test_test_coverage_allows_none_fields() -> None:
    """Allow None for any individual coverage field."""
    coverage = TestCoverageMetrics(manual_total=PARTIAL_MANUAL_TOTAL)

    assert coverage.manual_total == PARTIAL_MANUAL_TOTAL
    assert coverage.automated_total is None
    assert coverage.percentage_automation is None


def test_test_coverage_merge_fills_none_from_existing() -> None:
    """Merge fills None fields from existing record."""
    existing = TestCoverageMetrics(
        manual_total=EXISTING_MANUAL_TOTAL,
        automated_total=EXISTING_AUTOMATED_TOTAL,
        manual_created_last_month=EXISTING_MANUAL_CREATED,
        manual_updated_last_month=EXISTING_MANUAL_UPDATED,
        automated_created_last_month=EXISTING_AUTOMATED_CREATED,
        automated_updated_last_month=EXISTING_AUTOMATED_UPDATED,
        percentage_automation=EXISTING_PERCENTAGE,
    )
    partial = TestCoverageMetrics(manual_total=UPDATED_MANUAL_TOTAL)

    merged = partial.merge_with(existing)

    assert merged.manual_total == UPDATED_MANUAL_TOTAL
    assert merged.automated_total == EXISTING_AUTOMATED_TOTAL
    assert merged.manual_created_last_month == EXISTING_MANUAL_CREATED
    assert merged.percentage_automation == EXISTING_PERCENTAGE


def test_test_coverage_merge_preserves_zero() -> None:
    """Merge preserves explicitly provided zero values."""
    existing = TestCoverageMetrics(
        manual_total=EXISTING_MANUAL_TOTAL,
        automated_total=EXISTING_AUTOMATED_TOTAL,
    )
    update = TestCoverageMetrics(manual_total=0, automated_total=None)

    merged = update.merge_with(existing)

    assert merged.manual_total == 0
    assert merged.automated_total == EXISTING_AUTOMATED_TOTAL


def test_test_coverage_merge_with_none_existing() -> None:
    """Merge with None existing returns self unchanged."""
    partial = TestCoverageMetrics(manual_total=PARTIAL_MANUAL_TOTAL)

    merged = partial.merge_with(None)

    assert merged.manual_total == PARTIAL_MANUAL_TOTAL
    assert merged.automated_total is None
