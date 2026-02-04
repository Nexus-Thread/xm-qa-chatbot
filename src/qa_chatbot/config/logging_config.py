"""Logging configuration helpers for the QA chatbot."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Iterable


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "INFO"
    format: str = "json"


class JsonLogFormatter(logging.Formatter):
    """Format logs as structured JSON payloads."""

    def format(self, record: logging.LogRecord) -> str:
        """Format the log record as JSON."""
        payload = {
            "timestamp": datetime.now(tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extras = _extract_extras(record, payload.keys())
        if extras:
            payload.update(extras)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: LoggingSettings) -> None:
    """Configure application logging based on settings."""
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.level.upper())

    handler = logging.StreamHandler(sys.stdout)
    if settings.format == "json":
        handler.setFormatter(JsonLogFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))

    root_logger.handlers = [handler]


def _extract_extras(record: logging.LogRecord, known_fields: Iterable[str]) -> dict[str, Any]:
    """Extract extra fields from a log record."""
    known = set(known_fields)
    extras: dict[str, Any] = {}
    for key, value in record.__dict__.items():
        if key.startswith("_") or key in known or key in _DEFAULT_RECORD_FIELDS:
            continue
        extras[key] = value
    return extras


_DEFAULT_RECORD_FIELDS = {
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
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
}
