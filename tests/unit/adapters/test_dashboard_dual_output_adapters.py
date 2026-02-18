"""Tests for composite and Confluence dashboard adapters."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest

from qa_chatbot.adapters.output.dashboard.composite import CompositeDashboardAdapter
from qa_chatbot.adapters.output.dashboard.confluence import ConfluenceDashboardAdapter
from qa_chatbot.adapters.output.dashboard.exceptions import DashboardRenderError
from qa_chatbot.adapters.output.jira_mock import MockJiraAdapter
from qa_chatbot.application import GenerateMonthlyReportUseCase, GetDashboardDataUseCase
from qa_chatbot.application.ports import DashboardPort
from qa_chatbot.application.services.reporting_calculations import EdgeCasePolicy
from qa_chatbot.domain import ProjectId, Submission, TestCoverageMetrics, TimeWindow, build_default_stream_project_registry

if TYPE_CHECKING:
    from pathlib import Path

    from qa_chatbot.adapters.output.persistence.sqlite import SQLiteAdapter


@dataclass
class FakeDashboardAdapter(DashboardPort):
    """Fake adapter for validating fan-out behavior."""

    base_path: Path
    generated: list[str]

    def generate_overview(self, month: TimeWindow) -> Path:
        """Record overview generation and return output path."""
        self.generated.append(f"overview:{month.to_iso_month()}")
        return self.base_path / "overview.html"

    def generate_project_detail(self, project_id: ProjectId, months: list[TimeWindow]) -> Path:
        """Record project detail generation and return output path."""
        self.generated.append(f"team:{project_id.value}:{len(months)}")
        return self.base_path / f"project-{project_id.value}.html"

    def generate_trends(self, projects: list[ProjectId], months: list[TimeWindow]) -> Path:
        """Record trends generation and return output path."""
        self.generated.append(f"trends:{len(projects)}:{len(months)}")
        return self.base_path / "trends.html"


def _seed_submissions(sqlite_adapter: SQLiteAdapter) -> None:
    project_a = ProjectId("project-a")
    project_b = ProjectId("project-b")
    jan = TimeWindow.from_year_month(2026, 1)
    feb = TimeWindow.from_year_month(2026, 2)

    submission_a_jan = Submission.create(
        project_id=project_a,
        month=jan,
        test_coverage=TestCoverageMetrics(
            manual_total=120,
            automated_total=80,
            manual_created_in_reporting_month=10,
            manual_updated_in_reporting_month=5,
            automated_created_in_reporting_month=8,
            automated_updated_in_reporting_month=3,
            percentage_automation=40.0,
        ),
        overall_test_cases=None,
    )
    submission_b_jan = Submission.create(
        project_id=project_b,
        month=jan,
        test_coverage=TestCoverageMetrics(
            manual_total=95,
            automated_total=70,
            manual_created_in_reporting_month=6,
            manual_updated_in_reporting_month=4,
            automated_created_in_reporting_month=5,
            automated_updated_in_reporting_month=2,
            percentage_automation=42.0,
        ),
        overall_test_cases=None,
    )
    submission_a_feb = Submission.create(
        project_id=project_a,
        month=feb,
        test_coverage=TestCoverageMetrics(
            manual_total=140,
            automated_total=100,
            manual_created_in_reporting_month=12,
            manual_updated_in_reporting_month=6,
            automated_created_in_reporting_month=9,
            automated_updated_in_reporting_month=4,
            percentage_automation=41.0,
        ),
        overall_test_cases=None,
        created_at=datetime(2026, 2, 4, 12, 0, 0, tzinfo=UTC),
    )

    sqlite_adapter.save_submission(submission_a_jan)
    sqlite_adapter.save_submission(submission_b_jan)
    sqlite_adapter.save_submission(submission_a_feb)


def test_composite_dashboard_adapter_fans_out(tmp_path: Path) -> None:
    """Composite adapter should invoke all child adapters."""
    month = TimeWindow.from_year_month(2026, 2)
    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    projects = [ProjectId("project-a"), ProjectId("project-b")]

    generated_a: list[str] = []
    generated_b: list[str] = []
    adapter_a = FakeDashboardAdapter(base_path=tmp_path / "a", generated=generated_a)
    adapter_b = FakeDashboardAdapter(base_path=tmp_path / "b", generated=generated_b)
    composite = CompositeDashboardAdapter(adapters=(adapter_a, adapter_b))

    overview_path = composite.generate_overview(month)
    project_path = composite.generate_project_detail(ProjectId("project-a"), months)
    trends_path = composite.generate_trends(projects, months)

    assert overview_path == tmp_path / "a" / "overview.html"
    assert project_path == tmp_path / "a" / "project-project-a.html"
    assert trends_path == tmp_path / "a" / "trends.html"
    assert generated_a == ["overview:2026-02", "team:project-a:2", "trends:2:2"]
    assert generated_b == ["overview:2026-02", "team:project-a:2", "trends:2:2"]


def test_composite_dashboard_adapter_requires_children() -> None:
    """Composite adapter should fail when no delegates are configured."""
    composite = CompositeDashboardAdapter(adapters=())
    with pytest.raises(DashboardRenderError, match="At least one dashboard adapter"):
        composite.generate_overview(TimeWindow.from_year_month(2026, 2))


def test_confluence_dashboard_adapter_generates_local_artifacts(
    sqlite_adapter: SQLiteAdapter,
    tmp_path: Path,
) -> None:
    """Confluence adapter should generate local files for all views."""
    _seed_submissions(sqlite_adapter)
    registry = build_default_stream_project_registry()
    jira_adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
    )
    report_use_case = GenerateMonthlyReportUseCase(
        storage_port=sqlite_adapter,
        jira_port=jira_adapter,
        registry=registry,
        timezone="UTC",
        edge_case_policy=EdgeCasePolicy(),
        now_provider=lambda: datetime(2026, 2, 4, 12, 0, 0, tzinfo=UTC),
    )
    dashboard_data_use_case = GetDashboardDataUseCase(storage_port=sqlite_adapter)
    adapter = ConfluenceDashboardAdapter(
        get_dashboard_data_use_case=dashboard_data_use_case,
        generate_monthly_report_use_case=report_use_case,
        output_dir=tmp_path / "dashboards",
    )

    months = [TimeWindow.from_year_month(2026, 2), TimeWindow.from_year_month(2026, 1)]
    overview = adapter.generate_overview(TimeWindow.from_year_month(2026, 2))
    project = adapter.generate_project_detail(ProjectId("project-a"), months)
    trends = adapter.generate_trends([ProjectId("project-a"), ProjectId("project-b")], months)

    overview_content = overview.read_text(encoding="utf-8")
    project_content = project.read_text(encoding="utf-8")
    trends_content = trends.read_text(encoding="utf-8")

    assert overview.name == "overview.confluence.html"
    assert project.name == "project-project-a.confluence.html"
    assert trends.name == "trends.confluence.html"
    assert "Monthly QA Summary" in overview_content
    assert "Section B — Test Coverage" in overview_content
    assert "Project Detail — project-a" in project_content
    assert "<h1>Trends</h1>" in trends_content
