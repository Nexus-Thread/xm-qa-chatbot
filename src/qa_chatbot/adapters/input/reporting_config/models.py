"""Reporting configuration models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from qa_chatbot.domain.entities import BusinessStream, Project
from qa_chatbot.domain.registries import StreamRegistry


class ReportingConfig(BaseModel):
    """Configuration for monthly QA summary reporting."""

    model_config = ConfigDict(extra="forbid")

    version: str = Field(default="1.0")
    streams: list[StreamConfig]
    jira: JiraConfig
    regression_suites: list[RegressionSuiteConfig] = Field(default_factory=list)

    @property
    def all_projects(self) -> tuple[ProjectConfig, ...]:
        """Return all projects across streams ordered by stream and project order."""
        return tuple(project for _, project in self._ordered_stream_projects())

    def to_registry(self) -> StreamRegistry:
        """Build a stream registry from the configuration."""
        ordered_pairs = self._ordered_stream_projects()
        streams = tuple(BusinessStream(id=stream.id, name=stream.name, order=stream.order) for stream in self._ordered_streams())
        projects = tuple(
            Project(
                id=project.id,
                name=project.name,
                business_stream_id=stream.id,
            )
            for stream, project in ordered_pairs
        )
        return StreamRegistry(streams=streams, projects=projects)

    def _ordered_streams(self) -> list[StreamConfig]:
        """Return streams sorted by configured order."""
        return sorted(self.streams, key=lambda item: item.order)

    def _ordered_stream_projects(self) -> list[tuple[StreamConfig, ProjectConfig]]:
        """Return stream-project pairs ordered by project order."""
        ordered_pairs: list[tuple[StreamConfig, ProjectConfig]] = []
        for stream in self._ordered_streams():
            ordered_pairs.extend((stream, project) for project in stream.projects)
        return sorted(ordered_pairs, key=lambda item: item[1].order)


class StreamConfig(BaseModel):
    """Defines a business stream in the report."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    order: int = Field(ge=0)
    projects: list[ProjectConfig] = Field(default_factory=list)


class ProjectConfig(BaseModel):
    """Defines a project within a business stream."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    order: int = Field(ge=0)
    jira_sources: list[JiraProjectSourceConfig] = Field(default_factory=list)
    jira_filters: JiraProjectFiltersConfig
    defect_leakage: DefectLeakageScopeConfig


class JiraConfig(BaseModel):
    """Global Jira configuration defaults."""

    connection: JiraConnectionConfig
    priority_mapping: PriorityMappingConfig
    qa_found_logic: QaFoundLogicConfig
    time_window_field: str = Field(default="created")
    query_templates: JiraQueryTemplatesConfig

    @property
    def url(self) -> str:
        """Return Jira base URL for backward-compatible consumers."""
        return self.connection.base_url


class JiraConnectionConfig(BaseModel):
    """Connection details for Jira API access."""

    model_config = ConfigDict(extra="forbid")

    base_url: str
    username: str
    api_token: str


class JiraProjectFiltersConfig(BaseModel):
    """Project-specific Jira filters used by report metrics."""

    model_config = ConfigDict(extra="forbid")

    lower: JiraPriorityFilterGroupConfig
    prod: JiraPriorityFilterGroupConfig


class JiraPriorityFilterGroupConfig(BaseModel):
    """Priority-bucket filter strings for one Jira issue scope."""

    model_config = ConfigDict(extra="forbid")

    p1_p2: str
    p3_p4: str


class JiraProjectSourceConfig(BaseModel):
    """Jira project-specific source configuration."""

    key: str
    project_key: str
    components: list[str] = Field(default_factory=list)
    issue_types: list[str]


class PriorityMappingConfig(BaseModel):
    """Maps Jira priorities into reporting buckets."""

    p1_p2: list[str]
    p3_p4: list[str]


class QaFoundLogicConfig(BaseModel):
    """Defines how to identify QA-found issues in Jira."""

    reporter_groups: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    custom_field: str | None = Field(default=None)
    custom_field_values: list[str] = Field(default_factory=list)


class JiraQueryTemplatesConfig(BaseModel):
    """Templates for Jira queries and links."""

    bugs_found: str
    production_incidents: str
    capa: str
    defect_leakage_numerator: str
    defect_leakage_denominator: str


class DefectLeakageScopeConfig(BaseModel):
    """Defines numerator and denominator sources for leakage."""

    numerator: LeakageScopeSelection
    denominator: LeakageScopeSelection


class LeakageScopeSelection(BaseModel):
    """Reference to a Jira source for leakage calculations."""

    jira_source_key: str


class RegressionSuiteConfig(BaseModel):
    """Defines regression suite metadata."""

    key: str
    name: str
    category: str
    platform: str
