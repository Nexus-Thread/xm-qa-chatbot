"""DTOs for monthly QA reports."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BucketCountDTO:
    """Bucketed counts for P1-P2 and P3-P4."""

    p1_p2: float | int | None
    p3_p4: float | int | None


@dataclass(frozen=True)
class DefectLeakageDTO:
    """Defect leakage summary for rendering."""

    numerator: int | None
    denominator: int | None
    rate_percent: float | None


@dataclass(frozen=True)
class CapaDTO:
    """CAPA data for rendering."""

    count: int | None
    status: str
    link: str | None


@dataclass(frozen=True)
class RegressionTimeEntryDTO:
    """Regression time entry for rendering."""

    label: str
    duration: str


@dataclass(frozen=True)
class QualityMetricsRow:
    """Quality metrics row for report output."""

    business_stream: str
    project_name: str
    supported_releases_count: int | None
    bugs_found: BucketCountDTO
    production_incidents: BucketCountDTO
    capa: CapaDTO
    defect_leakage: DefectLeakageDTO
    regression_time: tuple[RegressionTimeEntryDTO, ...]
    is_portfolio: bool = False


@dataclass(frozen=True)
class TestCoverageRow:
    """Test coverage row for report output."""

    business_stream: str
    project_name: str
    percentage_automation: float | None
    manual_total: int | None
    manual_created_in_reporting_month: int | None
    manual_updated_in_reporting_month: int | None
    automated_total: int | None
    automated_created_in_reporting_month: int | None
    automated_updated_in_reporting_month: int | None
    is_portfolio: bool = False


@dataclass(frozen=True)
class ReportMetadata:
    """Report metadata payload."""

    reporting_period: str
    generated_at: str


@dataclass(frozen=True)
class CompletenessStatus:
    """Completeness summary for a report."""

    status: str
    missing: tuple[str, ...]
    missing_by_project: dict[str, tuple[str, ...]] | None = None


@dataclass(frozen=True)
class MonthlyReport:
    """Full monthly QA report payload."""

    metadata: ReportMetadata
    completeness: CompletenessStatus
    quality_metrics_rows: tuple[QualityMetricsRow, ...]
    test_coverage_rows: tuple[TestCoverageRow, ...]
    overall_test_cases: int | None
