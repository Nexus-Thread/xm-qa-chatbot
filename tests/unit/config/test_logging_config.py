"""Unit tests for logging configuration."""

from __future__ import annotations

import json
import logging

from qa_chatbot.config.logging_config import JsonLogFormatter, LoggingSettings, configure_logging


def test_json_log_formatter_includes_extras() -> None:
    """Serialize extra fields into JSON payloads."""
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="qa_chatbot",
        level=logging.INFO,
        pathname=__file__,
        lineno=10,
        msg="Hello",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-123"

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "Hello"
    assert payload["request_id"] == "req-123"
    assert payload["level"] == "INFO"


def test_configure_logging_sets_root_handler() -> None:
    """Ensure configure_logging installs a handler."""
    configure_logging(LoggingSettings(level="debug", format="text"))

    root_logger = logging.getLogger()

    assert root_logger.handlers
    assert root_logger.level == logging.DEBUG
