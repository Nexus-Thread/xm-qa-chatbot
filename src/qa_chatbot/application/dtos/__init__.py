"""Application DTOs."""

from .app_settings import AppSettings
from .dashboard_data import (
    OverviewDashboardData,
    ProjectDetailDashboardData,
    ProjectMonthlySnapshot,
    ProjectOverviewCard,
    TrendsDashboardData,
    TrendSeries,
)
from .extraction_result import CoverageExtractionResult, ExtractionResult, HistoryExtractionRequest
from .report_data import (
    BucketCountDTO,
    CompletenessStatus,
    DefectLeakageDTO,
    MonthlyReport,
    QualityMetricsRow,
    ReportMetadata,
    TestCoverageRow,
)
from .submission_command import SubmissionCommand
from .submission_result import SubmissionResult

__all__ = [
    "AppSettings",
    "BucketCountDTO",
    "CompletenessStatus",
    "CoverageExtractionResult",
    "DefectLeakageDTO",
    "ExtractionResult",
    "HistoryExtractionRequest",
    "MonthlyReport",
    "OverviewDashboardData",
    "ProjectDetailDashboardData",
    "ProjectMonthlySnapshot",
    "ProjectOverviewCard",
    "QualityMetricsRow",
    "ReportMetadata",
    "SubmissionCommand",
    "SubmissionResult",
    "TestCoverageRow",
    "TrendSeries",
    "TrendsDashboardData",
]
