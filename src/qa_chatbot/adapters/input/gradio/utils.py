"""Shared utilities for the Gradio adapter."""

from __future__ import annotations

from datetime import UTC, date, datetime


def today() -> date:
    """Return today's date in UTC."""
    return datetime.now(tz=UTC).date()


def sanitize_input(message: str, max_chars: int) -> str:
    """Normalize and truncate user input."""
    normalized = message.strip()
    if len(normalized) <= max_chars:
        return normalized
    return normalized[:max_chars].rstrip()
