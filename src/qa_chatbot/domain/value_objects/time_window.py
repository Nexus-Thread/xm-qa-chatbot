"""Time window value object."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidTimeWindowError

if TYPE_CHECKING:
    from datetime import date

# Time window validation constants
MIN_YEAR = 2000
MAX_YEAR = 2100
MIN_MONTH = 1
MAX_MONTH = 12


@dataclass(frozen=True)
class TimeWindow:
    """Represents a month-based reporting window."""

    year: int
    month: int

    def __post_init__(self) -> None:
        """Validate time window bounds."""
        if self.year < MIN_YEAR or self.year > MAX_YEAR:
            message = f"Year must be between {MIN_YEAR} and {MAX_YEAR}"
            raise InvalidTimeWindowError(message)
        if self.month < MIN_MONTH or self.month > MAX_MONTH:
            message = f"Month must be between {MIN_MONTH} and {MAX_MONTH}"
            raise InvalidTimeWindowError(message)

    @classmethod
    def from_date(cls, value: date) -> TimeWindow:
        """Create a time window from a date."""
        return cls(year=value.year, month=value.month)

    @classmethod
    def from_year_month(cls, year: int, month: int) -> TimeWindow:
        """Create a time window from explicit year/month values."""
        return cls(year=year, month=month)

    @classmethod
    def default_for(cls, today: date, grace_period_days: int = 2) -> TimeWindow:
        """Select the default window based on a grace period into the next month."""
        if grace_period_days < 0:
            message = "Grace period must be non-negative"
            raise InvalidTimeWindowError(message)

        if today.day <= grace_period_days:
            month = today.month - 1
            year = today.year
            if month == 0:
                month = 12
                year -= 1
            return cls(year=year, month=month)

        return cls.from_date(today)

    def to_iso_month(self) -> str:
        """Return the window in YYYY-MM format."""
        return f"{self.year:04d}-{self.month:02d}"
