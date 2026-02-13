"""Output adapters."""

from .dashboard import CompositeDashboardAdapter, ConfluenceDashboardAdapter, HtmlDashboardAdapter
from .jira_mock import MockJiraAdapter
from .llm import OpenAIAdapter
from .metrics import InMemoryMetricsAdapter
from .persistence import SQLiteAdapter

__all__ = [
    "CompositeDashboardAdapter",
    "ConfluenceDashboardAdapter",
    "HtmlDashboardAdapter",
    "InMemoryMetricsAdapter",
    "MockJiraAdapter",
    "OpenAIAdapter",
    "SQLiteAdapter",
]
