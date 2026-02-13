"""Hardcoded reporting metadata registry."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidConfigurationError
from qa_chatbot.domain.registries.stream_registry import build_default_registry


@dataclass(frozen=True)
class JiraPriorityFilterGroup:
    """Priority bucket filters for a Jira scope."""

    p1_p2: str
    p3_p4: str


@dataclass(frozen=True)
class ProjectJiraFilters:
    """Project-specific Jira filters used by reporting."""

    lower: JiraPriorityFilterGroup
    prod: JiraPriorityFilterGroup


@dataclass(frozen=True)
class ProjectReportingConfig:
    """Reporting metadata for a single project."""

    project_id: str
    jira_project_key: str
    jira_filters: ProjectJiraFilters
    defect_leakage_numerator_source: str
    defect_leakage_denominator_source: str


@dataclass(frozen=True)
class JiraQueryTemplates:
    """Templates used to build Jira links."""

    bugs_found: str
    production_incidents: str
    defect_leakage_numerator: str
    defect_leakage_denominator: str


@dataclass(frozen=True)
class ReportingRegistry:
    """Static reporting metadata for all projects."""

    projects: tuple[ProjectReportingConfig, ...]
    query_templates: JiraQueryTemplates
    time_window_field: str = "created"

    def project_config(self, project_id: str) -> ProjectReportingConfig:
        """Return project reporting config by project id."""
        normalized = project_id.strip().lower()
        for project in self.projects:
            if project.project_id == normalized:
                return project
        msg = f"Project {project_id} not found in reporting registry"
        raise InvalidConfigurationError(msg)


def build_default_reporting_registry() -> ReportingRegistry:
    """Return hardcoded reporting metadata."""
    query_templates = JiraQueryTemplates(
        bugs_found="project in ({project_keys}) AND created >= {start} AND created < {end}",
        production_incidents="project in ({project_keys}) AND created >= {start} AND created < {end}",
        defect_leakage_numerator="project in ({project_keys}) AND created >= {start} AND created < {end}",
        defect_leakage_denominator="project in ({project_keys}) AND created >= {start} AND created < {end}",
    )
    project_keys = {
        "jmanager_server_portal": "JMGR",
        "symbols_management_service": "SYM",
        "local_depositors_service": "LDS",
        "fees_management_service": "FEES",
        "admin_tools_service": "ADMIN",
        "data_access_layer": "DAL",
        "metaproxy": "META",
        "plugins": "PLUG",
        "client_trading": "CLTR",
        "payments": "PAY",
    }

    def _project_key(project_id: str) -> str:
        return project_keys.get(project_id, project_id.upper())

    def _filters(project_key: str) -> ProjectJiraFilters:
        p1_p2 = f"project = {project_key} AND priority in (P1, P2)"
        p3_p4 = f"project = {project_key} AND priority in (P3, P4)"
        group = JiraPriorityFilterGroup(p1_p2=p1_p2, p3_p4=p3_p4)
        return ProjectJiraFilters(lower=group, prod=group)

    registry = build_default_registry()
    projects = tuple(
        ProjectReportingConfig(
            project_id=project.id,
            jira_project_key=_project_key(project.id),
            jira_filters=_filters(_project_key(project.id)),
            defect_leakage_numerator_source=f"{project.id}_numerator",
            defect_leakage_denominator_source=f"{project.id}_denominator",
        )
        for project in registry.projects
    )
    return ReportingRegistry(
        projects=projects,
        query_templates=query_templates,
    )
