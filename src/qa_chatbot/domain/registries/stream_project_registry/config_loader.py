"""Config loading utilities for stream-project registry."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from qa_chatbot.domain.entities import JiraPriorityFilterGroup, JiraProjectFilters
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def load_project_filters() -> dict[str, JiraProjectFilters]:
    """Load project Jira filters from reporting config."""
    config_file = _config_path()
    try:
        with config_file.open(encoding="utf-8") as handle:
            loaded = yaml.safe_load(handle)
    except OSError as err:
        msg = f"Failed to read reporting config: {config_file}"
        raise InvalidConfigurationError(msg) from err

    if not isinstance(loaded, dict):
        msg = "reporting config root must be an object"
        raise InvalidConfigurationError(msg)

    return _extract_project_filters(loaded)


def project_filters_for(project_id: str, filters_by_project: dict[str, JiraProjectFilters]) -> JiraProjectFilters:
    """Return project filters or fail with a clear config error."""
    project_filters = filters_by_project.get(project_id)
    if project_filters is None:
        msg = f"Missing jira_filters config for project {project_id}"
        raise InvalidConfigurationError(msg)
    return project_filters


def _config_path() -> Path:
    return Path(__file__).resolve().parents[5] / "config" / "reporting_config.yaml"


def _as_str(value: object, path: str) -> str:
    if not isinstance(value, str):
        msg = f"Expected string at {path}"
        raise InvalidConfigurationError(msg)
    return value


def _extract_project_filters(config_data: dict[str, Any]) -> dict[str, JiraProjectFilters]:
    streams_data = config_data.get("streams")
    if not isinstance(streams_data, list):
        msg = "reporting config must include streams"
        raise InvalidConfigurationError(msg)

    filters_by_project: dict[str, JiraProjectFilters] = {}
    for stream_index, stream_data in enumerate(streams_data):
        if not isinstance(stream_data, dict):
            msg = f"stream entry at index {stream_index} must be an object"
            raise InvalidConfigurationError(msg)

        projects_data = stream_data.get("projects")
        if not isinstance(projects_data, list):
            msg = f"stream at index {stream_index} must include projects"
            raise InvalidConfigurationError(msg)

        for project_index, project_data in enumerate(projects_data):
            if not isinstance(project_data, dict):
                msg = f"project entry at index {project_index} in stream {stream_index} must be an object"
                raise InvalidConfigurationError(msg)

            project_id = _as_str(project_data.get("id"), f"streams[{stream_index}].projects[{project_index}].id")
            jira_filters_data = project_data.get("jira_filters")
            if not isinstance(jira_filters_data, dict):
                msg = f"project {project_id} must include jira_filters"
                raise InvalidConfigurationError(msg)

            lower_data = jira_filters_data.get("lower")
            prod_data = jira_filters_data.get("prod")
            if not isinstance(lower_data, dict) or not isinstance(prod_data, dict):
                msg = f"project {project_id} jira_filters must include lower and prod"
                raise InvalidConfigurationError(msg)

            filters_by_project[project_id] = JiraProjectFilters(
                lower=JiraPriorityFilterGroup(
                    p1_p2=_as_str(lower_data.get("p1_p2"), f"project {project_id} jira_filters.lower.p1_p2"),
                    p3_p4=_as_str(lower_data.get("p3_p4"), f"project {project_id} jira_filters.lower.p3_p4"),
                ),
                prod=JiraPriorityFilterGroup(
                    p1_p2=_as_str(prod_data.get("p1_p2"), f"project {project_id} jira_filters.prod.p1_p2"),
                    p3_p4=_as_str(prod_data.get("p3_p4"), f"project {project_id} jira_filters.prod.p3_p4"),
                ),
            )
    return filters_by_project
