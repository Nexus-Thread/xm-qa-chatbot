"""Time window value object."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..exceptions import InvalidTimeWindowError


@dataclass(frozen=True)
class TimeWindow:
    """Represents a month-based reporting window."""

    year: int
    month: int

    def __post_init__(self) -> None:
        if self.year < 2000 or self.year > 2100:
            raise InvalidTimeWindowError("Year must be between 2000 and 2100")
        if self.month < 1 or self.month > 12:
            raise InvalidTimeWindowError("Month must be between 1 and 12")

    @classmethod
    def from_date(cls, value: date) -> "TimeWindow":
        """Create a time window from a date."""

        return cls(year=value.year, month=value.month)

    @classmethod
    def from_year_month(cls, year: int, month: int) -> "TimeWindow":
        """Create a time window from explicit year/month values."""

        return cls(year=year, month=month)

    @classmethod
    def default_for(cls, today: date, grace_period_days: int = 2) -> "TimeWindow":
        """Select the default window based on a grace period into the next month."""

        if grace_period_days < 0:
            raise InvalidTimeWindowError("Grace period must be non-negative")

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