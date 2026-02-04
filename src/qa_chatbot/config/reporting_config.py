"""Reporting configuration loaded from YAML."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import BaseModel, Field

from qa_chatbot.domain.entities import BusinessStream, Project
from qa_chatbot.domain.exceptions import InvalidConfigurationError
from qa_chatbot.domain.registries import StreamRegistry

if TYPE_CHECKING:
    from pathlib import Path


class ReportingConfig(BaseModel):
    """Configuration for monthly QA summary reporting."""

    version: str = Field(default="1.0")
    streams: list[StreamConfig]
    projects: list[ProjectConfig]
    jira: JiraConfig
    release_sources: ReleaseSourceConfig
    regression_suites: list[RegressionSuiteConfig] = Field(default_factory=list)
    edge_case_policy: EdgeCasePolicyConfig

    @classmethod
    def load(cls, *, path: Path) -> ReportingConfig:
        """Load reporting configuration from YAML."""
        try:
            raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            message = f"Reporting config file not found: {path}"
            raise InvalidConfigurationError(message) from exc
        except (OSError, yaml.YAMLError) as exc:
            message = f"Unable to read reporting config from {path}: {exc}"
            raise InvalidConfigurationError(message) from exc

        try:
            return cls.model_validate(raw_data)
        except Exception as exc:  # pragma: no cover - surfaced at startup
            message = f"Invalid reporting configuration: {exc}"
            raise InvalidConfigurationError(message) from exc

    def to_registry(self) -> StreamRegistry:
        """Build a stream registry from the configuration."""
        streams = tuple(
            BusinessStream(
                id=stream.id,
                name=stream.name,
                order=stream.order,
            )
            for stream in sorted(self.streams, key=lambda item: item.order)
        )
        projects = tuple(
            Project(
                id=project.id,
                name=project.name,
                business_stream_id=project.business_stream_id,
                aliases=tuple(project.aliases),
                is_active=project.is_active,
            )
            for project in sorted(self.projects, key=lambda item: item.order)
        )
        return StreamRegistry(streams=streams, projects=projects)


class StreamConfig(BaseModel):
    """Defines a business stream in the report."""

    id: str
    name: str
    order: int = Field(ge=0)
    is_active: bool = Field(default=True)


class ProjectConfig(BaseModel):
    """Defines a project within a business stream."""

    id: str
    name: str
    business_stream_id: str
    order: int = Field(ge=0)
    aliases: list[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    jira_sources: list[JiraProjectSourceConfig] = Field(default_factory=list)
    release_source: ReleaseSourceSelection
    defect_leakage: DefectLeakageScopeConfig


class JiraConfig(BaseModel):
    """Global Jira configuration defaults."""

    url: str
    priority_mapping: PriorityMappingConfig
    qa_found_logic: QaFoundLogicConfig
    time_window_field: str = Field(default="created")
    query_templates: JiraQueryTemplatesConfig


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


class ReleaseSourceConfig(BaseModel):
    """Defines supported release data source options."""

    manual: ManualReleaseConfig
    jira_fix_version: JiraFixVersionConfig
    release_calendar: ReleaseCalendarConfig


class ReleaseSourceSelection(BaseModel):
    """Selects a release source for a project."""

    source: str
    manual_value: int | None = Field(default=None)


class ManualReleaseConfig(BaseModel):
    """Manual override for releases."""

    enabled: bool = Field(default=True)


class JiraFixVersionConfig(BaseModel):
    """Jira fixVersion based release counting."""

    enabled: bool = Field(default=False)


class ReleaseCalendarConfig(BaseModel):
    """External release calendar placeholder."""

    enabled: bool = Field(default=False)


class RegressionSuiteConfig(BaseModel):
    """Defines regression suite metadata."""

    key: str
    name: str
    category: str
    platform: str


class EdgeCasePolicyConfig(BaseModel):
    """Defines edge-case handling and rounding rules."""

    leakage_zero_denominator: str = Field(default="zero")
    automation_zero_total: str = Field(default="zero")
    rounding_decimals: int = Field(default=2, ge=0, le=6)
