"""JSON payload and schema validation utilities for structured extraction."""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from .exceptions import LLMExtractionError

SchemaT = TypeVar("SchemaT", bound=BaseModel)
MAX_LOGGED_PAYLOAD_CHARS = 512
LOGGER = logging.getLogger(__name__)


def parse_json_payload(payload: str) -> dict[str, Any]:
    """Parse JSON payload into a dictionary."""
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, TypeError) as err:
        msg = "LLM response contained invalid JSON"
        raise LLMExtractionError(msg) from err


def parse_schema_payload(
    payload: dict[str, Any],
    schema: type[SchemaT],
) -> SchemaT:
    """Validate payload against a Pydantic schema."""
    try:
        return schema.model_validate(payload)
    except ValidationError as err:
        LOGGER.exception(
            "Schema validation failed",
            extra={
                "schema": schema.__name__,
                "payload_keys": sorted(payload.keys()),
                "payload_preview": serialize_payload_preview(payload),
            },
        )
        msg = "LLM response did not match expected schema"
        raise LLMExtractionError(msg) from err


def serialize_payload_preview(payload: dict[str, Any]) -> str:
    """Serialize payload into a bounded preview string for logging."""
    try:
        raw_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        raw_payload = str(payload)

    if len(raw_payload) <= MAX_LOGGED_PAYLOAD_CHARS:
        return raw_payload
    return f"{raw_payload[:MAX_LOGGED_PAYLOAD_CHARS]}..."
