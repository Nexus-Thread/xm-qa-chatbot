"""Application ports."""

from .input import (
    ExtractStructuredDataPort,
    GenerateMonthlyReportPort,
    GetDashboardDataPort,
    SubmitProjectDataPort,
)
from .output import DashboardPort, MetricsPort, StoragePort, StructuredExtractionPort

__all__ = [
    "DashboardPort",
    "ExtractStructuredDataPort",
    "GenerateMonthlyReportPort",
    "GetDashboardDataPort",
    "MetricsPort",
    "StoragePort",
    "StructuredExtractionPort",
    "SubmitProjectDataPort",
]
