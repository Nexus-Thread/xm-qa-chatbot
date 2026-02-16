"""Project entity."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from qa_chatbot.domain.value_objects import StreamId


@dataclass(frozen=True)
class JiraPriorityFilterGroup:
    """Jira filters split by priority buckets."""

    p1_p2: str
    p3_p4: str

    def __post_init__(self) -> None:
        """Validate filter templates."""
        if not self.p1_p2.strip() or not self.p3_p4.strip():
            msg = "Jira priority filters must not be empty"
            raise InvalidConfigurationError(msg)


@dataclass(frozen=True)
class JiraProjectFilters:
    """Jira filter templates for a project."""

    lower: JiraPriorityFilterGroup
    prod: JiraPriorityFilterGroup

    def resolve(self, label: str) -> str:
        """Return a filter template by label."""
        mapping = {
            "lower_p1_p2": self.lower.p1_p2,
            "lower_p3_p4": self.lower.p3_p4,
            "prod_p1_p2": self.prod.p1_p2,
            "prod_p3_p4": self.prod.p3_p4,
        }
        if label not in mapping:
            msg = f"Unknown Jira query label: {label}"
            raise InvalidConfigurationError(msg)
        return mapping[label]

    def replace_time_window(self, label: str, start: str, end: str) -> str:
        """Replace time-window placeholders for the selected filter template."""
        template = self.resolve(label)
        return template.replace("{start}", start).replace("{end}", end)


@dataclass(frozen=True)
class Project:
    """Represents a project within a business stream."""

    id: str
    name: str
    business_stream_id: StreamId
    jira_filters: JiraProjectFilters | None = None

    def __post_init__(self) -> None:
        """Validate project fields."""
        if not self.id.strip() or not self.name.strip():
            msg = "Project id and name are required"
            raise InvalidConfigurationError(msg)
        if self.jira_filters is not None and not isinstance(self.jira_filters, JiraProjectFilters):
            msg = "jira_filters must be JiraProjectFilters when provided"
            raise InvalidConfigurationError(msg)
