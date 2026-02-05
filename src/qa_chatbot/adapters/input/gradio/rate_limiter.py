"""Rate limiting helpers for Gradio sessions."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .conversation_manager import ConversationSession


@dataclass
class RateLimiter:
    """Simple sliding-window rate limiter per session."""

    max_requests: int
    window_seconds: int
    _requests: dict[int, list[float]] = field(default_factory=dict)

    def allow(self, session: ConversationSession) -> bool:
        """Return whether the request is allowed for this session."""
        now = datetime.now(tz=UTC).timestamp()
        key = id(session)
        entries = [entry for entry in self._requests.get(key, []) if now - entry < self.window_seconds]
        if len(entries) >= self.max_requests:
            self._requests[key] = entries
            return False
        entries.append(now)
        self._requests[key] = entries
        return True
