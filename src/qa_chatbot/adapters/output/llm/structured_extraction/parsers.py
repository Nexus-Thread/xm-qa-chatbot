"""Parsing helpers for structured extraction payloads."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_chatbot.domain import DomainError, TimeWindow

from .exceptions import LLMExtractionError

if TYPE_CHECKING:
    from datetime import date

    from .schemas import TimeWindowSchema


def resolve_time_window(data: TimeWindowSchema, current_date: date) -> TimeWindow:
    """Resolve typed model output into a TimeWindow."""
    if data.kind == "current_month":
        return TimeWindow.from_date(current_date)
    if data.kind == "previous_month":
        return TimeWindow.default_for(current_date, grace_period_days=31)

    if data.month is None:
        message = "Time window month is required for iso_month kind"
        raise LLMExtractionError(message)

    try:
        year_str, month_str = data.month.split("-")
        return TimeWindow.from_year_month(int(year_str), int(month_str))
    except (DomainError, ValueError) as err:
        message = "Time window must be in YYYY-MM format"
        raise LLMExtractionError(message) from err
