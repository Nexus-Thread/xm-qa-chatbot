"""Reporting calculations and formatting helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.value_objects.metrics import BucketCount, DefectLeakage, RegressionTimeBlock
from qa_chatbot.domain.value_objects.portfolio_aggregates import PortfolioAggregates

if TYPE_CHECKING:
    from qa_chatbot.config.reporting_config import EdgeCasePolicyConfig


@dataclass(frozen=True)
class EdgeCasePolicy:
    """Defines how to handle calculation edge cases."""

    leakage_zero_denominator: str
    automation_zero_total: str
    rounding_decimals: int

    @classmethod
    def from_config(cls, config: EdgeCasePolicyConfig) -> EdgeCasePolicy:
        """Create policy from config."""
        return cls(
            leakage_zero_denominator=config.leakage_zero_denominator,
            automation_zero_total=config.automation_zero_total,
            rounding_decimals=config.rounding_decimals,
        )

    def compute_automation_percentage(self, manual_total: int, automated_total: int) -> float:
        """Compute automation percentage with edge-case handling."""
        total = manual_total + automated_total
        if total == 0:
            if self.automation_zero_total == "na":
                return float("nan")
            return 0.0
        return round((automated_total / total) * 100, self.rounding_decimals)

    def compute_defect_leakage_rate(self, numerator: int, denominator: int) -> float:
        """Compute defect leakage percentage with edge-case handling."""
        if denominator == 0:
            if self.leakage_zero_denominator == "na":
                return float("nan")
            return 0.0
        return round((numerator / denominator) * 100, self.rounding_decimals)


def format_regression_time(block: RegressionTimeBlock) -> tuple[tuple[str, str], ...]:
    """Format regression time entries into label/duration pairs."""
    if block.free_text_override:
        return ((block.free_text_override, ""),)
    formatted: list[tuple[str, str]] = []
    for entry in block.entries:
        duration = _format_duration(entry.duration_minutes)
        extras: list[str] = []
        if entry.context_count is not None:
            extras.append(f"({entry.context_count})")
        if entry.threads is not None:
            extras.append(f"{entry.threads} threads")
        if entry.notes:
            extras.append(entry.notes)
        label_suffix = f" {' '.join(extras)}" if extras else ""
        formatted.append((f"{entry.suite_name}{label_suffix}", duration))
    return tuple(formatted)


def _format_duration(minutes: float) -> str:
    if minutes < 1:
        seconds = round(minutes * 60)
        return f"{seconds}s"
    if minutes < 60:
        return f"{round(minutes)}m"
    hours = minutes / 60
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
