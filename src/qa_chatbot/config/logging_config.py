"""Logging configuration helpers for the QA chatbot."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class LoggingSettings:
    """Logging configuration settings."""

    level: str = "DEBUG"


def configure_logging(settings: LoggingSettings) -> None:
    """Configure application logging based on settings."""
    logging.basicConfig(
        level=settings.level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        stream=sys.stdout,
        force=True,
    )
