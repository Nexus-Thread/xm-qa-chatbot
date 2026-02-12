"""Unit tests for reporting configuration loading."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from qa_chatbot.config import ReportingConfig
from qa_chatbot.domain.exceptions import InvalidConfigurationError

if TYPE_CHECKING:
    from pathlib import Path


def test_reporting_config_loads_nested_stream_projects(tmp_path: Path) -> None:
    """Load nested stream projects and map stream ids into registry projects."""
    config_file = tmp_path / "reporting_config.yaml"
    config_file.write_text(
        """
version: "1.0"
streams:
  - id: stream_b
    name: Stream B
    order: 20
    projects:
      - id: project_b2
        name: Project B2
        order: 20
        jira_filters:
          lower:
            p1_p2: project = B2 AND priority in (P1, P2)
            p3_p4: project = B2 AND priority in (P3, P4)
          prod:
            p1_p2: project = B2 AND priority in (P1, P2)
            p3_p4: project = B2 AND priority in (P3, P4)
        defect_leakage:
          numerator:
            jira_source_key: b2_num
          denominator:
            jira_source_key: b2_den
      - id: project_b1
        name: Project B1
        order: 10
        jira_filters:
          lower:
            p1_p2: project = B1 AND priority in (P1, P2)
            p3_p4: project = B1 AND priority in (P3, P4)
          prod:
            p1_p2: project = B1 AND priority in (P1, P2)
            p3_p4: project = B1 AND priority in (P3, P4)
        defect_leakage:
          numerator:
            jira_source_key: b1_num
          denominator:
            jira_source_key: b1_den
  - id: stream_a
    name: Stream A
    order: 10
    projects:
      - id: project_a1
        name: Project A1
        order: 10
        jira_filters:
          lower:
            p1_p2: project = A1 AND priority in (P1, P2)
            p3_p4: project = A1 AND priority in (P3, P4)
          prod:
            p1_p2: project = A1 AND priority in (P1, P2)
            p3_p4: project = A1 AND priority in (P3, P4)
        defect_leakage:
          numerator:
            jira_source_key: a1_num
          denominator:
            jira_source_key: a1_den
jira:
  connection:
    base_url: https://jira.example.com
    username: jira-user@example.com
    api_token: token
  time_window_field: created
  priority_mapping:
    p1_p2: [P1]
    p3_p4: [P3]
  qa_found_logic:
    reporter_groups: []
    labels: []
    components: []
  query_templates:
    bugs_found: test
    production_incidents: test
    capa: test
    defect_leakage_numerator: test
    defect_leakage_denominator: test
        """.strip(),
        encoding="utf-8",
    )

    config = ReportingConfig.load(path=config_file)
    registry = config.to_registry()

    assert [stream.id for stream in registry.streams] == ["stream_a", "stream_b"]
    assert [project.id for project in config.all_projects] == ["project_a1", "project_b1", "project_b2"]
    assert [project.business_stream_id for project in registry.projects] == ["stream_a", "stream_b", "stream_b"]


def test_reporting_config_rejects_legacy_top_level_projects(tmp_path: Path) -> None:
    """Raise when legacy top-level projects key is present."""
    config_file = tmp_path / "reporting_config.yaml"
    config_file.write_text(
        """
version: "1.0"
streams:
  - id: stream_a
    name: Stream A
    order: 10
projects:
  - id: project_a1
    name: Project A1
    business_stream_id: stream_a
    order: 10
    jira_filters:
      lower:
        p1_p2: project = A1 AND priority in (P1, P2)
        p3_p4: project = A1 AND priority in (P3, P4)
      prod:
        p1_p2: project = A1 AND priority in (P1, P2)
        p3_p4: project = A1 AND priority in (P3, P4)
    defect_leakage:
      numerator:
        jira_source_key: a1_num
      denominator:
        jira_source_key: a1_den
jira:
  connection:
    base_url: https://jira.example.com
    username: jira-user@example.com
    api_token: token
  time_window_field: created
  priority_mapping:
    p1_p2: [P1]
    p3_p4: [P3]
  qa_found_logic:
    reporter_groups: []
    labels: []
    components: []
  query_templates:
    bugs_found: test
    production_incidents: test
    capa: test
    defect_leakage_numerator: test
    defect_leakage_denominator: test
        """.strip(),
        encoding="utf-8",
    )

    with pytest.raises(InvalidConfigurationError):
        ReportingConfig.load(path=config_file)
