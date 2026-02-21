"""Unit tests for mock Jira adapter links and generated metrics."""

from __future__ import annotations

from urllib.parse import unquote_plus
from uuid import UUID

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

BUGS_P1_P2_MIN = 0
BUGS_P1_P2_MAX = 6
BUGS_P3_P4_MIN = 2
BUGS_P3_P4_MAX = 14
INCIDENTS_P1_P2_MIN = 0
INCIDENTS_P1_P2_MAX = 3
INCIDENTS_P3_P4_MIN = 0
INCIDENTS_P3_P4_MAX = 8
LEAKAGE_DENOMINATOR_MIN = 8
LEAKAGE_DENOMINATOR_MAX = 40
LEAKAGE_RATE_MIN = 0.0
LEAKAGE_RATE_MAX = 100.0
TEST_JIRA_API_TOKEN = UUID(int=0).hex


def _build_adapter(registry: StreamProjectRegistry) -> MockJiraAdapter:
    return MockJiraAdapter(
        registry=registry,
        jira_base_url="https://jira.example.com",
        jira_username="jira-user@example.com",
        jira_api_token=TEST_JIRA_API_TOKEN,
    )


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
    adapter = _build_adapter(registry)
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
    adapter = _build_adapter(registry)
    period = ReportingPeriod.for_month(2026, 1, "UTC")

    with pytest.raises(InvalidConfigurationError, match="Unknown Jira query label"):
        adapter.build_issue_link(ProjectId("client_trading"), period, "unknown_label")


def test_fetch_metrics_returns_valid_values_for_known_project() -> None:
    """Return non-negative generated metrics in expected ranges."""
    registry = build_default_stream_project_registry()
    adapter = _build_adapter(registry)
    period = ReportingPeriod.for_month(2026, 1, "UTC")

    bugs = adapter.fetch_bugs_found(ProjectId("client_trading"), period)
    incidents = adapter.fetch_production_incidents(ProjectId("client_trading"), period)
    leakage = adapter.fetch_defect_leakage(ProjectId("client_trading"), period)

    assert BUGS_P1_P2_MIN <= bugs.p1_p2 <= BUGS_P1_P2_MAX
    assert BUGS_P3_P4_MIN <= bugs.p3_p4 <= BUGS_P3_P4_MAX
    assert INCIDENTS_P1_P2_MIN <= incidents.p1_p2 <= INCIDENTS_P1_P2_MAX
    assert INCIDENTS_P3_P4_MIN <= incidents.p3_p4 <= INCIDENTS_P3_P4_MAX
    assert LEAKAGE_DENOMINATOR_MIN <= leakage.denominator <= LEAKAGE_DENOMINATOR_MAX
    assert LEAKAGE_RATE_MIN <= leakage.numerator <= leakage.denominator
    assert LEAKAGE_RATE_MIN <= leakage.rate_percent <= LEAKAGE_RATE_MAX


def test_fetch_metrics_varies_by_period_for_same_project() -> None:
    """Return different generated metrics for different reporting months."""
    registry = build_default_stream_project_registry()
    adapter = _build_adapter(registry)

    jan = ReportingPeriod.for_month(2026, 1, "UTC")
    feb = ReportingPeriod.for_month(2026, 2, "UTC")

    jan_snapshot = (
        adapter.fetch_bugs_found(ProjectId("client_trading"), jan),
        adapter.fetch_production_incidents(ProjectId("client_trading"), jan),
        adapter.fetch_defect_leakage(ProjectId("client_trading"), jan),
    )
    feb_snapshot = (
        adapter.fetch_bugs_found(ProjectId("client_trading"), feb),
        adapter.fetch_production_incidents(ProjectId("client_trading"), feb),
        adapter.fetch_defect_leakage(ProjectId("client_trading"), feb),
    )

    assert jan_snapshot != feb_snapshot
