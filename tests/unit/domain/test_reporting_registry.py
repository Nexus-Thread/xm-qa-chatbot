"""Unit tests for hardcoded reporting registry."""

import pytest

from qa_chatbot.domain import build_default_reporting_registry
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def test_reporting_registry_contains_project_metadata() -> None:
    """Return metadata for known project."""
    registry = build_default_reporting_registry()

    project = registry.project_config("client_trading")

    assert project.project_id == "client_trading"
    assert project.jira_project_key == "CLTR"
    assert "priority in (P1, P2)" in project.jira_filters.lower.p1_p2


def test_reporting_registry_raises_for_unknown_project() -> None:
    """Raise for unknown project id."""
    registry = build_default_reporting_registry()

    with pytest.raises(InvalidConfigurationError):
        registry.project_config("missing-project")
