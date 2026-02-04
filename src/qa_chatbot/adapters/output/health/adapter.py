"""HTTP health check adapter."""

from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from qa_chatbot.adapters.output.metrics import InMemoryMetricsAdapter
    from qa_chatbot.application.ports import StoragePort


@dataclass(frozen=True)
class HealthCheckSettings:
    """Settings for the health check HTTP server."""

    host: str = "127.0.0.1"
    port: int = 8081


@dataclass
class HealthCheckAdapter:
    """Serve a lightweight health check endpoint."""

    storage_port: StoragePort
    metrics_adapter: InMemoryMetricsAdapter | None = None
    settings: HealthCheckSettings = field(default_factory=HealthCheckSettings)
    _logger: logging.Logger = field(init=False, repr=False)
    _server: HTTPServer | None = field(init=False, default=None, repr=False)
    _thread: threading.Thread | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        """Initialize logging for health checks."""
        self._logger = logging.getLogger(self.__class__.__name__)

    def start(self) -> None:
        """Start the health check server in a background thread."""
        if self._server is not None:
            return

        handler = self._build_handler()
        self._server = HTTPServer((self.settings.host, self.settings.port), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self._logger.info(
            "Health check server started",
            extra={"host": self.settings.host, "port": self.settings.port},
        )

    def stop(self) -> None:
        """Stop the health check server if running."""
        if self._server is None:
            return
        self._server.shutdown()
        self._server.server_close()
        self._server = None
        self._thread = None

    def _build_handler(self) -> type[BaseHTTPRequestHandler]:
        """Build a request handler bound to this adapter."""
        adapter = self

        class HealthHandler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:
                if self.path != "/health":
                    self.send_response(404)
                    self.end_headers()
                    return

                payload = adapter.build_payload()
                data = json.dumps(payload).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *_: object) -> None:
                return

        return HealthHandler

    def build_payload(self) -> dict[str, object]:
        """Create the health check response payload."""
        database_ok = self._check_database()
        payload: dict[str, object] = {
            "status": "ok" if database_ok else "degraded",
            "database_ok": database_ok,
        }
        if self.metrics_adapter is not None:
            snapshot = self.metrics_adapter.snapshot()
            payload["metrics"] = {
                "submissions": snapshot.submissions,
                "last_submission_at": snapshot.last_submission_at.isoformat() if snapshot.last_submission_at else None,
                "llm_latency_ms": snapshot.llm_latency_ms,
            }
        return payload

    def _check_database(self) -> bool:
        """Perform a lightweight database connectivity check."""
        try:
            _ = self.storage_port.get_all_teams()
        except Exception as exc:  # pragma: no cover - defensive logging
            self._logger.warning("Health check database query failed", extra={"error": str(exc)})
            return False
        return True
