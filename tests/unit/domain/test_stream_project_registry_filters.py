"""Unit tests for stream-project registry Jira filters."""

import pytest

from qa_chatbot.domain import build_default_stream_project_registry
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def test_stream_project_registry_project_contains_jira_filters() -> None:
    """Load project-level Jira filters from stream-project registry."""
    registry = build_default_stream_project_registry()

    project = registry.find_project("client_trading")

    assert project is not None
    assert project.jira_filters is not None
    assert "project = CLTR" in project.jira_filters.lower.p1_p2
    assert "priority in (P1, P2)" in project.jira_filters.lower.p1_p2
    assert "{start}" not in project.jira_filters.lower.p1_p2
    assert "{end}" not in project.jira_filters.lower.p1_p2


def test_jira_project_filters_reject_unknown_label() -> None:
    """Raise for unknown Jira filter label."""
    registry = build_default_stream_project_registry()
    project = registry.find_project("client_trading")
    assert project is not None
    assert project.jira_filters is not None

    with pytest.raises(InvalidConfigurationError, match="Unknown Jira query label"):
        project.jira_filters.resolve("unknown_label")
