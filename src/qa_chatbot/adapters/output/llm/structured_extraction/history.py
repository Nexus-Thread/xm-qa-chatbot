"""History normalization helpers for structured extraction."""

from __future__ import annotations

from .exceptions import InvalidHistoryError

ALLOWED_HISTORY_ROLES = {"system", "user", "assistant"}


def normalize_history(history: list[dict[str, str]] | None) -> list[dict[str, str]]:
    """Normalize history into chat message dictionaries."""
    if not history:
        return []

    normalized: list[dict[str, str]] = []
    for index, entry in enumerate(history):
        role = entry.get("role")
        content = entry.get("content")

        if not isinstance(role, str) or role.strip() not in ALLOWED_HISTORY_ROLES:
            msg = f"History entry at index {index} must contain a valid role"
            raise InvalidHistoryError(msg)

        if not isinstance(content, str) or not content.strip():
            msg = f"History entry at index {index} must contain non-empty content"
            raise InvalidHistoryError(msg)

        normalized.append(
            {
                "role": role.strip(),
                "content": content.strip(),
            }
        )

    return normalized
