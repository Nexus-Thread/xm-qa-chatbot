"""Jira metrics port contract."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from qa_chatbot.domain import BucketCount, DefectLeakage, ProjectId, ReportingPeriod


class JiraMetricsPort(Protocol):
    """Port for Jira-derived metrics."""

    def fetch_bugs_found(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return bugs found by QAs for the project and period."""

    def fetch_production_incidents(self, project_id: ProjectId, period: ReportingPeriod) -> BucketCount:
        """Return production incident counts for the project and period."""

    def fetch_defect_leakage(self, project_id: ProjectId, period: ReportingPeriod) -> DefectLeakage:
        """Return defect leakage metrics for the project and period."""

    def build_issue_link(self, project_id: ProjectId, period: ReportingPeriod, label: str) -> str:
        """Return a Jira filter link for a metric label."""
