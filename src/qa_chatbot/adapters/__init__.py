"""Adapters for external integrations."""

from .input import GradioAdapter, GradioSettings
from .output import OpenAIStructuredExtractionAdapter, SQLiteAdapter

__all__ = ["GradioAdapter", "GradioSettings", "OpenAIStructuredExtractionAdapter", "SQLiteAdapter"]
