"""Parsing helpers for structured extraction payloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.domain import TimeWindow

from .exceptions import LLMExtractionError

if TYPE_CHECKING:
    from datetime import date


def resolve_time_window(value: str, current_date: date) -> TimeWindow:
    """Resolve model output value into a TimeWindow."""
    cleaned = value.strip().lower()
    if cleaned in {"current", "current_month"}:
        return TimeWindow.from_date(current_date)
    if cleaned in {"previous", "previous_month", "last"}:
        return TimeWindow.default_for(current_date, grace_period_days=31)
    try:
        year_str, month_str = value.split("-")
        return TimeWindow.from_year_month(int(year_str), int(month_str))
    except ValueError as err:
        message = "Time window must be in YYYY-MM format"
        raise LLMExtractionError(message) from err
