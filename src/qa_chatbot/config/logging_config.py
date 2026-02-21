"""Logging configuration helpers for the QA chatbot."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime

_STANDARD_LOG_RECORD_FIELDS = {
    "args",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    """Format log records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        """Serialize a log record into a JSON string."""
        payload: dict[str, object] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        extras = {
            key: value for key, value in record.__dict__.items() if key not in _STANDARD_LOG_RECORD_FIELDS and not key.startswith("_")
        }
        payload.update(extras)

        if record.exc_info is not None:
            payload["exception"] = self.formatException(record.exc_info)
        if record.stack_info is not None:
            payload["stack"] = self.formatStack(record.stack_info)

        return json.dumps(payload, default=str)


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "INFO"
    log_format: str = "text"


def configure_logging(settings: LoggingSettings) -> None:
    """Configure application logging based on settings."""
    formatter: logging.Formatter = (
        JsonFormatter() if settings.log_format == "json" else logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatter)

    logging.basicConfig(
        level=settings.level,
        handlers=[handler],
        force=True,
    )
