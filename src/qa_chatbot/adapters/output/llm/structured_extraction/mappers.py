"""Mapping helpers for structured extraction payloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.domain import TestCoverageMetrics

if TYPE_CHECKING:
    from .schemas import TestCoverageSchema


def to_test_coverage_metrics(data: TestCoverageSchema) -> TestCoverageMetrics:
    """Convert coverage schema payload into domain metrics."""
    return TestCoverageMetrics(
        manual_total=data.manual_total,
        automated_total=data.automated_total,
        manual_created_in_reporting_month=data.manual_created_in_reporting_month,
        manual_updated_in_reporting_month=data.manual_updated_in_reporting_month,
        automated_created_in_reporting_month=data.automated_created_in_reporting_month,
        automated_updated_in_reporting_month=data.automated_updated_in_reporting_month,
        percentage_automation=None,
    )
