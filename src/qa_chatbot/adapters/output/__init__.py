"""Output adapters."""

from .dashboard import HtmlDashboardAdapter
from .jira_mock import MockJiraAdapter
from .llm import OpenAIAdapter
from .metrics import InMemoryMetricsAdapter
from .persistence import SQLiteAdapter
from .releases_mock import MockReleaseAdapter

__all__ = [
    "HtmlDashboardAdapter",
    "InMemoryMetricsAdapter",
    "MockJiraAdapter",
    "MockReleaseAdapter",
    "OpenAIAdapter",
    "SQLiteAdapter",
]
