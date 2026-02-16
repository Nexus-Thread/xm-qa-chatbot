"""Unit tests for mock Jira adapter query links."""

from __future__ import annotations

from urllib.parse import unquote_plus

import pytest

from qa_chatbot.adapters.output.jira_mock import MockJiraAdapter
from qa_chatbot.domain import (
    BusinessStream,
    JiraPriorityFilterGroup,
    JiraProjectFilters,
    Project,
    ProjectId,
    ReportingPeriod,
    StreamId,
    StreamProjectRegistry,
    build_default_stream_project_registry,
)
from qa_chatbot.domain.exceptions import InvalidConfigurationError


def test_build_issue_link_uses_project_filter_and_reporting_month_bounds() -> None:
    """Build Jira link by replacing provided time-window placeholders."""
    registry = StreamProjectRegistry(
        streams=(
            BusinessStream(
                id=StreamId("client_journey"),
                name="Client Journey",
                order=1,
            ),
        ),
        projects=(
            Project(
                id="client_trading",
                name="Client Trading",
                business_stream_id=StreamId("client_journey"),
                jira_filters=JiraProjectFilters(
                    lower=JiraPriorityFilterGroup(
                        p1_p2='project = CLIENT_TRADING AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                        p3_p4='project = CLIENT_TRADING AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                    ),
                    prod=JiraPriorityFilterGroup(
                        p1_p2='project = CLIENT_TRADING AND env = prod AND priority in (P1, P2) AND created >= "{start}" AND created < "{end}"',
                        p3_p4='project = CLIENT_TRADING AND env = prod AND priority in (P3, P4) AND created >= "{start}" AND created < "{end}"',
                    ),
                ),
            ),
        ),
    )
    adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
    )
    period = ReportingPeriod.for_month(2026, 1, "UTC")

    link = adapter.build_issue_link(ProjectId("client_trading"), period, "lower_p1_p2")

    assert link.startswith("https://jira.example.com/issues/?jql=")
    query = unquote_plus(link.split("jql=", maxsplit=1)[1])
    assert "project = CLIENT_TRADING" in query
    assert "priority in (P1, P2)" in query
    assert "{start}" not in query
    assert "{end}" not in query
    assert 'created >= "2026-01-01T00:00:00+00:00"' in query
    assert 'created < "2026-02-01T00:00:00+00:00"' in query


def test_build_issue_link_raises_for_unknown_label() -> None:
    """Raise for unknown issue-link label."""
    registry = build_default_stream_project_registry()
    adapter = MockJiraAdapter(
        registry=registry,
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token="token",  # noqa: S106
    )
    period = ReportingPeriod.for_month(2026, 1, "UTC")

    with pytest.raises(InvalidConfigurationError, match="Unknown Jira query label"):
        adapter.build_issue_link(ProjectId("client_trading"), period, "unknown_label")
