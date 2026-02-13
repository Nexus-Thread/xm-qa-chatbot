"""Dashboard output adapters."""

from .composite import CompositeDashboardAdapter
from .confluence import ConfluenceDashboardAdapter
from .exceptions import DashboardRenderError
from .html import HtmlDashboardAdapter

__all__ = [
    "CompositeDashboardAdapter",
    "ConfluenceDashboardAdapter",
    "DashboardRenderError",
    "HtmlDashboardAdapter",
]
