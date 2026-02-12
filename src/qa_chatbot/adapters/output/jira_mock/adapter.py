"""Mock Jira metrics adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.ports.output import JiraMetricsPort
from qa_chatbot.domain import BucketCount, CapaStatus, DefectLeakage, ProjectId, ReportingPeriod
from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from qa_chatbot.adapters.input.reporting_config import JiraProjectSourceConfig, ReportingConfig


@dataclass(frozen=True)
class MockJiraAdapter(JiraMetricsPort):
    """Return canned Jira metrics for report generation."""

    config: ReportingConfig

    def fetch_bugs_found(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return bugs found by QAs for the project and period."""
        _ = self._find_project_source(project_id)
        _ = period
        return BucketCount(p1_p2=2, p3_p4=5)

    def fetch_production_incidents(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return production incident counts for the project and period."""
        _ = self._find_project_source(project_id)
        _ = period
        return BucketCount(p1_p2=1, p3_p4=3)

    def fetch_capa(self, project_id: ProjectId, period: ReportingPeriod) -> CapaStatus:
        """Return CAPA status for the project and period."""
        _ = self._find_project_source(project_id)
        _ = period
        return CapaStatus(count=1, status="OK")

    def fetch_defect_leakage(self, project_id: ProjectId, period: ReportingPeriod) -> DefectLeakage:
        """Return defect leakage metrics for the project and period."""
        _ = self._find_project_source(project_id)
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
        project_source = self._find_project_source(project_id)
        project_keys = project_source.project_key if project_source else project_id.value
        query = template.format(project_keys=project_keys, start=period.start_datetime, end=period.end_datetime)
        return f"{self.config.jira.url}/issues/?jql={query}"

    def _find_project_source(self, project_id: ProjectId) -> JiraProjectSourceConfig | None:
        for project in self.config.all_projects:
            if project.id == project_id.value:
                if not project.jira_sources:
                    return None
                return project.jira_sources[0]
        msg = f"Project {project_id.value} not found in reporting config"
        raise InvalidConfigurationError(msg)

    def _resolve_template(self, label: str) -> str:
        templates = self.config.jira.query_templates
        mapping = {
            "bugs_found": templates.bugs_found,
            "production_incidents": templates.production_incidents,
            "capa": templates.capa,
            "defect_leakage_numerator": templates.defect_leakage_numerator,
            "defect_leakage_denominator": templates.defect_leakage_denominator,
        }
        if label not in mapping:
            msg = f"Unknown Jira query label: {label}"
            raise InvalidConfigurationError(msg)
        return mapping[label]
