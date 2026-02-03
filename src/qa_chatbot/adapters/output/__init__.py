"""Output adapters."""

from .llm import OpenAIAdapter
from .persistence import SQLiteAdapter

__all__ = ["OpenAIAdapter", "SQLiteAdapter"]
