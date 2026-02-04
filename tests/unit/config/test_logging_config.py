"""Unit tests for logging configuration."""

from __future__ import annotations

import logging

from qa_chatbot.config.logging_config import LoggingSettings, configure_logging


def test_configure_logging_sets_root_handler() -> None:
    """Ensure configure_logging installs a handler."""
    configure_logging(LoggingSettings(level="DEBUG"))

    root_logger = logging.getLogger()

    assert root_logger.handlers
    assert root_logger.level == logging.DEBUG
