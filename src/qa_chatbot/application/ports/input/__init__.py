"""Input ports for the application layer."""

from .extract_structured_data_port import ExtractStructuredDataPort
from .generate_monthly_report_port import GenerateMonthlyReportPort
from .get_dashboard_data_port import GetDashboardDataPort
from .submit_project_data_port import SubmitProjectDataPort

__all__ = [
    "ExtractStructuredDataPort",
    "GenerateMonthlyReportPort",
    "GetDashboardDataPort",
    "SubmitProjectDataPort",
]
