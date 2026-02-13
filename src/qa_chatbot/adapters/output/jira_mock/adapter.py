"""Mock Jira metrics adapter."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.application.ports.output import JiraMetricsPort
from qa_chatbot.domain import (
    BucketCount,
    DefectLeakage,
    ProjectId,
    ReportingPeriod,
    ReportingRegistry,
)
from qa_chatbot.domain.exceptions import InvalidConfigurationError


@dataclass(frozen=True)
class MockJiraAdapter(JiraMetricsPort):
    """Return canned Jira metrics for report generation."""

    reporting_registry: ReportingRegistry
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
        template = self._resolve_template(label)
        project_keys = self.reporting_registry.project_config(project_id.value).jira_project_key
        query = template.format(project_keys=project_keys, start=period.start_datetime, end=period.end_datetime)
        return f"{self.jira_base_url}/issues/?jql={query}"

    def _ensure_project_exists(self, project_id: ProjectId) -> None:
        _ = self.reporting_registry.project_config(project_id.value)

    def _resolve_template(self, label: str) -> str:
        templates = self.reporting_registry.query_templates
        mapping = {
            "bugs_found": templates.bugs_found,
            "production_incidents": templates.production_incidents,
            "defect_leakage_numerator": templates.defect_leakage_numerator,
            "defect_leakage_denominator": templates.defect_leakage_denominator,
        }
        if label not in mapping:
            msg = f"Unknown Jira query label: {label}"
            raise InvalidConfigurationError(msg)
        return mapping[label]
