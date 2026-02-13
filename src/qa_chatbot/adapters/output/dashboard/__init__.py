"""Dashboard output adapters."""

from .composite import CompositeDashboardAdapter
from .confluence import ConfluenceDashboardAdapter
from .html import HtmlDashboardAdapter

__all__ = [
    "CompositeDashboardAdapter",
    "ConfluenceDashboardAdapter",
    "HtmlDashboardAdapter",
]
