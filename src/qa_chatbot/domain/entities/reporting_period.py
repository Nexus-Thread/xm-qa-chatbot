"""Reporting period entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from qa_chatbot.domain.exceptions import InvalidTimeWindowError


@dataclass(frozen=True)
class ReportingPeriod:
    """Represents a calendar month reporting period."""

    year: int
    month: int
    start_datetime: datetime
    end_datetime: datetime
    timezone: str

    def __post_init__(self) -> None:
        """Validate period bounds."""
        if self.month < 1 or self.month > 12:
            message = "Month must be between 1 and 12"
            raise InvalidTimeWindowError(message)
        if self.end_datetime <= self.start_datetime:
            message = "Reporting period end must be after start"
            raise InvalidTimeWindowError(message)

    @classmethod
    def for_month(cls, year: int, month: int, timezone: str) -> ReportingPeriod:
        """Construct a reporting period for a month."""
        if month < 1 or month > 12:
            message = "Month must be between 1 and 12"
            raise InvalidTimeWindowError(message)
        zone = ZoneInfo(timezone)
        start = datetime(year, month, 1, tzinfo=zone)
        end = datetime(year + 1, 1, 1, tzinfo=zone) if month == 12 else datetime(year, month + 1, 1, tzinfo=zone)
        return cls(
            year=year,
            month=month,
            start_datetime=start,
            end_datetime=end,
            timezone=timezone,
        )

    @classmethod
    def from_time_window(cls, window: object, timezone: str) -> ReportingPeriod:
        """Create a reporting period from a TimeWindow-like object."""
        year = getattr(window, "year", None)
        month = getattr(window, "month", None)
        if year is None or month is None:
            message = "Time window must include year and month"
            raise InvalidTimeWindowError(message)
        return cls.for_month(int(year), int(month), timezone)

    @property
    def iso_month(self) -> str:
        """Return the reporting month in YYYY-MM format."""
        return f"{self.year:04d}-{self.month:02d}"

    @property
    def generated_at(self) -> datetime:
        """Return the generation timestamp in UTC."""
        return datetime.now(tz=UTC)
