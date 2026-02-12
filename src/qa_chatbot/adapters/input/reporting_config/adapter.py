"""Reporting configuration file adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml

from qa_chatbot.domain.exceptions import InvalidConfigurationError

from .models import ReportingConfig

if TYPE_CHECKING:
    from pathlib import Path


class ReportingConfigFileAdapter:
    """Load reporting configuration from YAML files."""

    def load(self, *, path: Path) -> ReportingConfig:
        """Load and validate reporting configuration from path."""
        try:
            raw_data = yaml.safe_load(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            message = f"Reporting config file not found: {path}"
            raise InvalidConfigurationError(message) from exc
        except (OSError, yaml.YAMLError) as exc:
            message = f"Unable to read reporting config from {path}: {exc}"
            raise InvalidConfigurationError(message) from exc

        try:
            return ReportingConfig.model_validate(raw_data)
        except Exception as exc:  # pragma: no cover - surfaced at startup
            message = f"Invalid reporting configuration: {exc}"
            raise InvalidConfigurationError(message) from exc
