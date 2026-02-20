"""Input port for monthly report generation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.application.dtos import MonthlyReport
    from qa_chatbot.domain import TimeWindow


class GenerateMonthlyReportPort(Protocol):
    """Contract for monthly report generation use cases."""

    def execute(self, month: TimeWindow) -> MonthlyReport:
        """Generate monthly report for the given time window."""
