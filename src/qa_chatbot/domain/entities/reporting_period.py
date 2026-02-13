"""Reporting period entity."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from qa_chatbot.domain.exceptions import InvalidTimeWindowError

# Month validation constants
MIN_MONTH = 1
MAX_MONTH = 12
DECEMBER = 12


@dataclass(frozen=True)
class ReportingPeriod:
    """Represents a calendar month reporting period."""

    year: int
    month: int
    start_datetime: datetime
    end_datetime: datetime
    timezone: str

    def __post_init__(self) -> None:
        """Validate period bounds and internal consistency."""
        self._validate_month(self.month)
        zone = self._resolve_timezone(self.timezone)

        start_zone = getattr(self.start_datetime.tzinfo, "key", None)
        end_zone = getattr(self.end_datetime.tzinfo, "key", None)
        if start_zone != self.timezone or end_zone != self.timezone:
            message = "Reporting period datetimes must use the configured timezone"
            raise InvalidTimeWindowError(message)

        if self.end_datetime <= self.start_datetime:
            message = "Reporting period end must be after start"
            raise InvalidTimeWindowError(message)

        expected_start = datetime(self.year, self.month, 1, tzinfo=zone)
        if self.start_datetime != expected_start:
            message = "Reporting period start must match the first day of year/month"
            raise InvalidTimeWindowError(message)

        expected_end = self._next_month_start(self.year, self.month, zone)
        if self.end_datetime != expected_end:
            message = "Reporting period end must match the first day of the next month"
            raise InvalidTimeWindowError(message)

    @classmethod
    def for_month(cls, year: int, month: int, timezone: str) -> ReportingPeriod:
        """Construct a reporting period for a month."""
        cls._validate_month(month)
        zone = cls._resolve_timezone(timezone)
        start = datetime(year, month, 1, tzinfo=zone)
        end = cls._next_month_start(year, month, zone)
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
        try:
            normalized_year = int(year)
            normalized_month = int(month)
        except (TypeError, ValueError) as err:
            message = "Time window year and month must be integers"
            raise InvalidTimeWindowError(message) from err
        return cls.for_month(normalized_year, normalized_month, timezone)

    @property
    def iso_month(self) -> str:
        """Return the reporting month in YYYY-MM format."""
        return f"{self.year:04d}-{self.month:02d}"

    @staticmethod
    def _validate_month(month: int) -> None:
        """Validate month range."""
        if month < MIN_MONTH or month > MAX_MONTH:
            message = f"Month must be between {MIN_MONTH} and {MAX_MONTH}"
            raise InvalidTimeWindowError(message)

    @staticmethod
    def _resolve_timezone(timezone: str) -> ZoneInfo:
        """Resolve timezone string to ZoneInfo."""
        try:
            return ZoneInfo(timezone)
        except ZoneInfoNotFoundError as err:
            message = f"Unknown timezone: {timezone}"
            raise InvalidTimeWindowError(message) from err

    @staticmethod
    def _next_month_start(year: int, month: int, zone: ZoneInfo) -> datetime:
        """Compute the first instant of the next month."""
        if month == DECEMBER:
            return datetime(year + 1, 1, 1, tzinfo=zone)
        return datetime(year, month + 1, 1, tzinfo=zone)
