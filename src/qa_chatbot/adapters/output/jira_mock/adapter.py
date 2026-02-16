"""Mock Jira metrics adapter."""

from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import quote_plus

from qa_chatbot.application.ports.output import JiraMetricsPort
from qa_chatbot.domain import (
    BucketCount,
    DefectLeakage,
    Project,
    ProjectId,
    ReportingPeriod,
    StreamProjectRegistry,
)
from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class MockJiraAdapter(JiraMetricsPort):
    """Return canned Jira metrics for report generation."""

    registry: StreamProjectRegistry
    jira_base_url: str
    jira_username: str
    jira_api_token: str

    def fetch_bugs_found(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return bugs found by QAs for the project and period."""
        self._ensure_project_exists(project_id)
        _ = period
        return BucketCount(p1_p2=2, p3_p4=5)

    def fetch_production_incidents(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return production incident counts for the project and period."""
        self._ensure_project_exists(project_id)
        _ = period
        return BucketCount(p1_p2=1, p3_p4=3)

    def fetch_defect_leakage(self, project_id: ProjectId, period: ReportingPeriod) -> DefectLeakage:
        """Return defect leakage metrics for the project and period."""
        self._ensure_project_exists(project_id)
        _ = period
        numerator = 2
        denominator = 12
        rate_percent = round((numerator / denominator) * 100, 2) if denominator else 0.0
        return DefectLeakage(
            numerator=numerator,
            denominator=denominator,
            rate_percent=rate_percent,
        )

    def build_issue_link(self, project_id: ProjectId, period: ReportingPeriod, label: str) -> str:
        """Return a Jira filter link for a metric label."""
        project = self._project(project_id)
        if project.jira_filters is None:
            msg = f"Project {project.id} does not have jira_filters configured"
            raise InvalidConfigurationError(msg)
        query = project.jira_filters.replace_time_window(
            label=label,
            start=period.start_datetime.isoformat(),
            end=period.end_datetime.isoformat(),
        )
        encoded_query = quote_plus(query)
        return f"{self.jira_base_url}/issues/?jql={encoded_query}"

    def _ensure_project_exists(self, project_id: ProjectId) -> None:
        _ = self._project(project_id)

    def _project(self, project_id: ProjectId) -> Project:
        project = self.registry.find_project(project_id.value)
        if project is None:
            msg = f"Project {project_id.value} not found in stream-project registry"
            raise InvalidConfigurationError(msg)
        return project
