"""Reporting calculations and formatting helpers."""

from __future__ import annotations

from qa_chatbot.domain.value_objects.metrics import (
    BucketCount,
    DefectLeakage,
    RegressionTimeBlock,
    RegressionTimeEntry,
)
from qa_chatbot.domain.value_objects.portfolio_aggregates import PortfolioAggregates

# Time conversion constants
SECONDS_PER_MINUTE = 60
MINUTES_PER_HOUR = 60
ROUNDING_DECIMALS = 2


class EdgeCasePolicy:
    """Defines how to handle calculation edge cases."""

    rounding_decimals = ROUNDING_DECIMALS

    def _compute_percentage(self, numerator: int, denominator: int) -> float:
        """Compute percentage with zero-denominator handling."""
        if denominator == 0:
            return float("nan")
        return round((numerator / denominator) * 100, ROUNDING_DECIMALS)

    def compute_automation_percentage(self, manual_total: int, automated_total: int) -> float:
        """Compute automation percentage with edge-case handling."""
        total = manual_total + automated_total
        return self._compute_percentage(numerator=automated_total, denominator=total)

    def compute_defect_leakage_rate(self, numerator: int, denominator: int) -> float:
        """Compute defect leakage percentage with edge-case handling."""
        return self._compute_percentage(numerator=numerator, denominator=denominator)


def format_regression_time(block: RegressionTimeBlock) -> tuple[tuple[str, str], ...]:
    """Format regression time entries into label/duration pairs."""
    if block.free_text_override:
        return ((block.free_text_override, ""),)
    formatted: list[tuple[str, str]] = []
    for entry in block.entries:
        duration = _format_duration(entry.duration_minutes)
        label = _build_regression_label(entry)
        formatted.append((label, duration))
    return tuple(formatted)


def _build_regression_label(entry: RegressionTimeEntry) -> str:
    extras: list[str] = []
    if entry.context_count is not None:
        extras.append(f"({entry.context_count})")
    if entry.threads is not None:
        extras.append(f"{entry.threads} threads")
    if entry.notes:
        extras.append(entry.notes)
    suffix = f" {' '.join(extras)}" if extras else ""
    return f"{entry.suite_name}{suffix}"


def _format_duration(minutes: float) -> str:
    if minutes < 1:
        seconds = round(minutes * SECONDS_PER_MINUTE)
        return f"{seconds}s"
    if minutes < MINUTES_PER_HOUR:
        return f"{round(minutes)}m"
    hours = minutes / MINUTES_PER_HOUR
    return f"{round(hours, 1)}h"


def compute_portfolio_aggregates(
    *,
    supported_releases: list[int],
    bugs: list[BucketCount],
    incidents: list[BucketCount],
    leakage: list[DefectLeakage],
    rounding_decimals: int,
) -> PortfolioAggregates:
    """Compute portfolio aggregate totals and averages."""
    supported_total = sum(supported_releases)
    project_count = len(supported_releases)
    avg_releases = round(supported_total / project_count, rounding_decimals) if project_count else 0.0

    bugs_avg = _average_bucket_counts(bugs, rounding_decimals)
    incidents_avg = _average_bucket_counts(incidents, rounding_decimals)
    leakage_total = _aggregate_leakage(leakage, rounding_decimals)

    return PortfolioAggregates(
        all_streams_supported_releases_total=supported_total,
        all_streams_supported_releases_avg=avg_releases,
        all_streams_bugs_avg=bugs_avg,
        all_streams_incidents_avg=incidents_avg,
        all_streams_defect_leakage=leakage_total,
    )


def _average_bucket_counts(values: list[BucketCount], rounding_decimals: int) -> BucketCount:
    if not values:
        return BucketCount(p1_p2=0, p3_p4=0)
    p1_total = sum(item.p1_p2 for item in values)
    p3_total = sum(item.p3_p4 for item in values)
    count = len(values)
    return BucketCount(
        p1_p2=int(round(p1_total / count, rounding_decimals)),
        p3_p4=int(round(p3_total / count, rounding_decimals)),
    )


def _aggregate_leakage(values: list[DefectLeakage], rounding_decimals: int) -> DefectLeakage:
    numerator = sum(item.numerator for item in values)
    denominator = sum(item.denominator for item in values)
    rate = round((numerator / denominator) * 100, rounding_decimals) if denominator else 0.0
    return DefectLeakage(numerator=numerator, denominator=denominator, rate_percent=rate)
