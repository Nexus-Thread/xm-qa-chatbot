"""Stream-project registry model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from qa_chatbot.domain.entities import BusinessStream, Project
    from qa_chatbot.domain.value_objects.stream_id import StreamId


@dataclass(frozen=True)
class StreamProjectRegistry:
    """Registry of business streams and projects."""

    streams: tuple[BusinessStream, ...]
    projects: tuple[Project, ...]

    def __post_init__(self) -> None:
        """Validate registry consistency."""
        stream_ids = {stream.id for stream in self.streams}
        if len(stream_ids) != len(self.streams):
            msg = "Business stream IDs must be unique"
            raise InvalidConfigurationError(msg)
        project_ids = {project.id for project in self.projects}
        if len(project_ids) != len(self.projects):
            msg = "Project IDs must be unique"
            raise InvalidConfigurationError(msg)
        for project in self.projects:
            if project.business_stream_id not in stream_ids:
                msg = f"Project {project.id} references unknown stream {project.business_stream_id}"
                raise InvalidConfigurationError(msg)

    def active_projects(self) -> tuple[Project, ...]:
        """Return active projects."""
        return self.projects

    def projects_for_stream(self, stream_id: StreamId) -> tuple[Project, ...]:
        """Return projects for a given stream."""
        return tuple(project for project in self.projects if project.business_stream_id == stream_id)

    def stream_name(self, stream_id: StreamId) -> str:
        """Return the stream name for an id."""
        for stream in self.streams:
            if stream.id == stream_id:
                return stream.name
        msg = f"Unknown stream id {stream_id.value}"
        raise InvalidConfigurationError(msg)

    def find_project(self, project_id: str) -> Project | None:
        """Find a project by id or name."""
        normalized = project_id.strip().lower()
        for project in self.projects:
            if project.id.lower() == normalized or project.name.lower() == normalized:
                return project
        return None
