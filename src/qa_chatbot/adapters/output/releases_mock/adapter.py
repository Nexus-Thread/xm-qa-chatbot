"""Mock release support adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from qa_chatbot.application.ports.output import ReleaseSupportPort
from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from qa_chatbot.config import ReportingConfig

if TYPE_CHECKING:
    from qa_chatbot.config.reporting_config import ProjectConfig
    from qa_chatbot.domain import ProjectId, ReportingPeriod


@dataclass(frozen=True)
class MockReleaseAdapter(ReleaseSupportPort):
    """Return canned supported release counts."""

    config: ReportingConfig

    def fetch_supported_releases(self, project_id: ProjectId, period: ReportingPeriod) -> int:
        """Return supported releases count for the project and period."""
        _ = project_id
        _ = period
        project_config = self._find_project_config(project_id)
        if project_config.release_source.source == "manual":
            return project_config.release_source.manual_value or 0
        msg = f"Unsupported release source {project_config.release_source.source}"
        raise InvalidConfigurationError(msg)

    def _find_project_config(self, project_id: ProjectId) -> ProjectConfig:
        for project in self.config.projects:
            if project.id == project_id.value:
                return project
        msg = f"Project {project_id.value} not found in reporting config"
        raise InvalidConfigurationError(msg)
