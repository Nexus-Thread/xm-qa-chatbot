"""Rate limiting helpers for Gradio sessions."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock
from typing import TYPE_CHECKING
from weakref import ref

if TYPE_CHECKING:
    from .conversation_manager import ConversationSession


@dataclass
class _SessionRequests:
    """Track request timestamps for a live session."""

    session_ref: ref[ConversationSession]
    entries: deque[float] = field(default_factory=deque)


@dataclass
class RateLimiter:
    """Simple sliding-window rate limiter per session."""

    max_requests: int
    window_seconds: int
    _requests: dict[int, _SessionRequests] = field(default_factory=dict)
    _lock: Lock = field(default_factory=Lock)

    def _clear_session(self, session_key: int) -> None:
        """Remove tracking for a collected session."""
        with self._lock:
            self._requests.pop(session_key, None)

    def allow(self, session: ConversationSession) -> bool:
        """Return whether the request is allowed for this session."""
        now = datetime.now(tz=UTC).timestamp()
        key = id(session)
        with self._lock:
            tracking = self._requests.get(key)
            if tracking is None or tracking.session_ref() is not session:

                def on_collect(_ref: object) -> None:
                    self._clear_session(key)

                tracking = _SessionRequests(session_ref=ref(session, on_collect))
                self._requests[key] = tracking

            while tracking.entries and now - tracking.entries[0] >= self.window_seconds:
                tracking.entries.popleft()

            if len(tracking.entries) >= self.max_requests:
                return False

            tracking.entries.append(now)
            return True
