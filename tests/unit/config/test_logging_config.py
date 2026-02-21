"""Unit tests for logging configuration."""

from __future__ import annotations

import json
import logging

from qa_chatbot.config.logging_config import JsonFormatter, LoggingSettings, configure_logging


def _raise_value_error() -> None:
    """Raise a value error for exception serialization testing."""
    message = "boom"
    raise ValueError(message)


def test_configure_logging_sets_root_handler() -> None:
    """Ensure configure_logging installs a handler."""
    configure_logging(LoggingSettings(level="DEBUG"))

    root_logger = logging.getLogger()

    assert root_logger.handlers
    assert root_logger.level == logging.DEBUG


def test_configure_logging_uses_json_formatter_when_enabled() -> None:
    """Install JSON formatter when json format is configured."""
    configure_logging(LoggingSettings(level="INFO", log_format="json"))

    root_logger = logging.getLogger()

    formatter = root_logger.handlers[0].formatter
    assert isinstance(formatter, JsonFormatter)

    record = logging.LogRecord(
        name="qa_chatbot.tests",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.component = "test_component"

    payload = json.loads(formatter.format(record))
    assert payload["level"] == "INFO"
    assert payload["logger"] == "qa_chatbot.tests"
    assert payload["message"] == "hello"
    assert payload["component"] == "test_component"


def test_configure_logging_uses_text_formatter_by_default() -> None:
    """Install standard text formatter by default."""
    configure_logging(LoggingSettings(level="INFO"))

    root_logger = logging.getLogger()
    formatter = root_logger.handlers[0].formatter

    assert formatter is not None
    assert not isinstance(formatter, JsonFormatter)


def test_json_formatter_serializes_exceptions() -> None:
    """Include exception information in JSON-formatted payloads."""
    formatter = JsonFormatter()

    try:
        _raise_value_error()
    except ValueError as err:
        exc_info = (type(err), err, err.__traceback__)

    record = logging.LogRecord(
        name="qa_chatbot.tests",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="failure",
        args=(),
        exc_info=exc_info,
    )

    payload = json.loads(formatter.format(record))
    assert payload["message"] == "failure"
    assert "ValueError: boom" in payload["exception"]
