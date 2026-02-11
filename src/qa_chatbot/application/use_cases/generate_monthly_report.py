"""Generate the monthly QA report."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isnan
from typing import TYPE_CHECKING

from qa_chatbot.application.dtos import (
    BucketCountDTO,
    CapaDTO,
    CompletenessStatus,
    DefectLeakageDTO,
    MonthlyReport,
    QualityMetricsRow,
    RegressionTimeEntryDTO,
    ReportMetadata,
    TestCoverageRow,
)
from qa_chatbot.application.services.reporting_calculations import (
    EdgeCasePolicy,
    compute_portfolio_aggregates,
    format_regression_time,
)
from qa_chatbot.domain import (
    BucketCount,
    DefectLeakage,
    ProjectId,
    RegressionTimeBlock,
    RegressionTimeEntry,
    ReportingPeriod,
    TestCoverageMetrics,
    TimeWindow,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from qa_chatbot.application.ports.output import JiraMetricsPort, StoragePort
    from qa_chatbot.domain import Project, StreamRegistry


@dataclass(frozen=True)
class GenerateMonthlyReportUseCase:
    """Build a monthly QA report from available sources."""

    storage_port: StoragePort
    jira_port: JiraMetricsPort
    registry: StreamRegistry
    timezone: str
    edge_case_policy: EdgeCasePolicy
    regression_suites: tuple[RegressionTimeEntry, ...] = ()
    completeness_mode: str = "partial"
    now_provider: Callable[[], datetime] = field(default_factory=lambda: lambda: datetime.now(tz=UTC))

    def execute(self, month: TimeWindow) -> MonthlyReport:
        """Generate a monthly report payload."""
        period = ReportingPeriod.from_time_window(month, timezone=self.timezone)
        quality_rows: list[QualityMetricsRow] = []
        coverage_rows: list[TestCoverageRow] = []
        missing: list[str] = []
        missing_by_project: dict[str, list[str]] = {}

        for project in self.registry.active_projects():
            quality_rows.append(self._build_quality_row(project, period, month, missing, missing_by_project))
            coverage_rows.append(self._build_coverage_row(project, month, missing, missing_by_project))

        quality_rows = self._with_portfolio_quality_row(quality_rows)
        coverage_rows = self._with_portfolio_coverage_row(coverage_rows)

        metadata = ReportMetadata(
            reporting_period=period.iso_month,
            generated_at=self.now_provider().isoformat(),
        )
        completeness = self._build_completeness(missing, missing_by_project)
        overall_test_cases = self._extract_overall_test_cases(month)

        return MonthlyReport(
            metadata=metadata,
            completeness=completeness,
            quality_metrics_rows=tuple(quality_rows),
            test_coverage_rows=tuple(coverage_rows),
            overall_test_cases=overall_test_cases,
        )

    def _build_quality_row(
        self,
        project: Project,
        period: ReportingPeriod,
        month: TimeWindow,
        missing: list[str],
        missing_by_project: dict[str, list[str]],
    ) -> QualityMetricsRow:
        stream_name = self.registry.stream_name(project.business_stream_id)
        supported_releases = self._extract_supported_releases(project_id=ProjectId(project.id), month=month)
        bugs_found = self._safe_fetch(
            missing,
            f"bugs_found:{project.id}",
            lambda: self.jira_port.fetch_bugs_found(ProjectId(project.id), period),
            project.id,
            missing_by_project,
        )
        incidents = self._safe_fetch(
            missing,
            f"production_incidents:{project.id}",
            lambda: self.jira_port.fetch_production_incidents(ProjectId(project.id), period),
            project.id,
            missing_by_project,
        )
        capa = self._safe_fetch(
            missing,
            f"capa:{project.id}",
            lambda: self.jira_port.fetch_capa(ProjectId(project.id), period),
            project.id,
            missing_by_project,
        )
        defect_leakage = self._safe_fetch(
            missing,
            f"defect_leakage:{project.id}",
            lambda: self.jira_port.fetch_defect_leakage(ProjectId(project.id), period),
            project.id,
            missing_by_project,
        )

        return QualityMetricsRow(
            business_stream=stream_name,
            project_name=project.name,
            supported_releases_count=self._safe_int(supported_releases),
            bugs_found=self._bucket_to_dto(bugs_found),
            production_incidents=self._bucket_to_dto(incidents),
            capa=CapaDTO(
                count=getattr(capa, "count", None),
                status=getattr(capa, "status", "MISSING"),
                link=self.jira_port.build_issue_link(ProjectId(project.id), period, "capa"),
            ),
            defect_leakage=self._defect_to_dto(defect_leakage),
            regression_time=self._build_regression_time_entries(),
        )

    def _build_coverage_row(
        self,
        project: Project,
        month: TimeWindow,
        missing: list[str],
        missing_by_project: dict[str, list[str]],
    ) -> TestCoverageRow:
        submissions = self.storage_port.get_submissions_by_project(ProjectId(project.id), month)
        latest = max(submissions, key=lambda item: item.created_at) if submissions else None
        coverage = latest.test_coverage if latest else None
        if coverage is None:
            missing.append(f"test_coverage:{project.id}")
            missing_by_project.setdefault(project.id, []).append("test_coverage")
        percentage = self._compute_automation_percentage(coverage)

        return TestCoverageRow(
            business_stream=self.registry.stream_name(project.business_stream_id),
            project_name=project.name,
            percentage_automation=percentage,
            manual_total=coverage.manual_total if coverage else None,
            manual_created_last_month=coverage.manual_created_last_month if coverage else None,
            manual_updated_last_month=coverage.manual_updated_last_month if coverage else None,
            automated_total=coverage.automated_total if coverage else None,
            automated_created_last_month=coverage.automated_created_last_month if coverage else None,
            automated_updated_last_month=coverage.automated_updated_last_month if coverage else None,
        )

    def _extract_overall_test_cases(self, month: TimeWindow) -> int | None:
        submissions = self.storage_port.get_submissions_by_month(month)
        latest_by_project: dict[str, TestCoverageMetrics] = {}
        latest_created_at: dict[str, datetime] = {}
        for submission in submissions:
            if submission.test_coverage is None:
                continue
            project_id = submission.project_id.value
            recorded_at = submission.created_at
            if project_id not in latest_created_at or recorded_at > latest_created_at[project_id]:
                latest_created_at[project_id] = recorded_at
                latest_by_project[project_id] = submission.test_coverage

        totals = [
            coverage.manual_total + coverage.automated_total
            for coverage in latest_by_project.values()
            if coverage.manual_total is not None and coverage.automated_total is not None
        ]
        if not totals:
            return None
        return sum(totals)

    def _extract_supported_releases(self, project_id: ProjectId, month: TimeWindow) -> int | None:
        submissions = self.storage_port.get_submissions_by_project(project_id, month)
        if not submissions:
            return None
        latest = max(submissions, key=lambda item: item.created_at)
        return latest.supported_releases_count

    def _build_completeness(
        self,
        missing: list[str],
        missing_by_project: dict[str, list[str]],
    ) -> CompletenessStatus:
        if not missing:
            return CompletenessStatus(status="COMPLETE", missing=(), missing_by_project=None)
        summary = {project: tuple(sorted(set(items))) for project, items in missing_by_project.items()}
        if self.completeness_mode == "fail":
            return CompletenessStatus(status="FAILED", missing=tuple(sorted(missing)), missing_by_project=summary)
        return CompletenessStatus(status="PARTIAL", missing=tuple(sorted(set(missing))), missing_by_project=summary)

    def _bucket_to_dto(self, bucket: object) -> BucketCountDTO:
        return BucketCountDTO(
            p1_p2=self._safe_number(getattr(bucket, "p1_p2", None)),
            p3_p4=self._safe_number(getattr(bucket, "p3_p4", None)),
        )

    def _defect_to_dto(self, defect: object) -> DefectLeakageDTO:
        numerator = self._safe_int(getattr(defect, "numerator", None))
        denominator = self._safe_int(getattr(defect, "denominator", None))
        rate_percent: float | None
        if numerator is not None and denominator is not None:
            rate_percent = self.edge_case_policy.compute_defect_leakage_rate(numerator, denominator)
        else:
            fallback_rate = self._safe_number(getattr(defect, "rate_percent", None))
            rate_percent = float(fallback_rate) if isinstance(fallback_rate, (int, float)) else None
        return DefectLeakageDTO(
            numerator=numerator,
            denominator=denominator,
            rate_percent=rate_percent,
        )

    def _compute_automation_percentage(self, coverage: TestCoverageMetrics | None) -> float | None:
        if coverage is None:
            return None
        if coverage.manual_total is None or coverage.automated_total is None:
            return None
        percentage = self.edge_case_policy.compute_automation_percentage(
            manual_total=coverage.manual_total,
            automated_total=coverage.automated_total,
        )
        if isnan(percentage):
            return None
        return percentage

    def _build_regression_time_entries(self) -> tuple[RegressionTimeEntryDTO, ...]:
        block = RegressionTimeBlock(entries=self.regression_suites)
        entries = format_regression_time(block)
        return tuple(RegressionTimeEntryDTO(label=label, duration=duration) for label, duration in entries)

    def _with_portfolio_quality_row(self, rows: list[QualityMetricsRow]) -> list[QualityMetricsRow]:
        supported = [row.supported_releases_count or 0 for row in rows if not row.is_portfolio]
        bugs = [
            BucketCount(p1_p2=int(row.bugs_found.p1_p2 or 0), p3_p4=int(row.bugs_found.p3_p4 or 0))
            for row in rows
            if not row.is_portfolio
        ]
        incidents = [
            BucketCount(p1_p2=int(row.production_incidents.p1_p2 or 0), p3_p4=int(row.production_incidents.p3_p4 or 0))
            for row in rows
            if not row.is_portfolio
        ]
        leakage = [
            DefectLeakage(
                numerator=int(row.defect_leakage.numerator or 0),
                denominator=int(row.defect_leakage.denominator or 0),
                rate_percent=float(row.defect_leakage.rate_percent or 0.0),
            )
            for row in rows
            if not row.is_portfolio
        ]
        aggregates = compute_portfolio_aggregates(
            supported_releases=supported,
            bugs=bugs,
            incidents=incidents,
            leakage=leakage,
            rounding_decimals=self.edge_case_policy.rounding_decimals,
        )
        portfolio_row = QualityMetricsRow(
            business_stream="All Streams",
            project_name="average",
            supported_releases_count=int(aggregates.all_streams_supported_releases_avg),
            bugs_found=BucketCountDTO(
                p1_p2=aggregates.all_streams_bugs_avg.p1_p2,
                p3_p4=aggregates.all_streams_bugs_avg.p3_p4,
            ),
            production_incidents=BucketCountDTO(
                p1_p2=aggregates.all_streams_incidents_avg.p1_p2,
                p3_p4=aggregates.all_streams_incidents_avg.p3_p4,
            ),
            capa=CapaDTO(count=None, status="N/A", link=None),
            defect_leakage=DefectLeakageDTO(
                numerator=aggregates.all_streams_defect_leakage.numerator,
                denominator=aggregates.all_streams_defect_leakage.denominator,
                rate_percent=aggregates.all_streams_defect_leakage.rate_percent,
            ),
            regression_time=(),
            is_portfolio=True,
        )
        return [portfolio_row, *rows]

    @staticmethod
    def _with_portfolio_coverage_row(rows: list[TestCoverageRow]) -> list[TestCoverageRow]:
        return rows

    @staticmethod
    def _safe_fetch(
        missing: list[str],
        label: str,
        func: Callable[[], object],
        project_id: str,
        missing_by_project: dict[str, list[str]],
    ) -> object:
        try:
            return func()
        except Exception:  # noqa: BLE001
            # Intentionally broad: mark data as missing rather than failing entire report
            missing.append(label)
            missing_by_project.setdefault(project_id, []).append(label.split(":", maxsplit=1)[0])
            return None

    @staticmethod
    def _safe_int(value: object) -> int | None:
        if isinstance(value, int):
            return value
        return None

    @staticmethod
    def _safe_number(value: object) -> float | int | None:
        if isinstance(value, (int, float)):
            return value
        return None
