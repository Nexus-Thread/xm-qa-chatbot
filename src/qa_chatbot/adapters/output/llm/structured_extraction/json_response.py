"""JSON and schema parsing utilities for structured extraction."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import BaseModel, ValidationError

from .exceptions import LLMExtractionError
from .settings import TokenUsage

SchemaT = TypeVar("SchemaT", bound=BaseModel)
MAX_LOGGED_PAYLOAD_CHARS = 512

if TYPE_CHECKING:
    import logging


def extract_message_content(response: Any) -> str:  # noqa: ANN401
    """Extract content from the first model response choice."""
    choices = getattr(response, "choices", None)
    if not choices:
        msg = "LLM response did not include choices"
        raise LLMExtractionError(msg)

    message = getattr(choices[0], "message", None)
    if message is None:
        msg = "LLM response did not include a message"
        raise LLMExtractionError(msg)

    content = getattr(message, "content", None)
    if content is None:
        msg = "LLM response did not include content"
        raise LLMExtractionError(msg)

    return content


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
    logger: logging.Logger,
) -> SchemaT:
    """Validate payload against a Pydantic schema."""
    try:
        return schema.model_validate(payload)
    except ValidationError as err:
        logger.exception(
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


def extract_usage(response: Any) -> TokenUsage | None:  # noqa: ANN401
    """Extract token usage from model response metadata."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return None

    return TokenUsage(
        prompt_tokens=getattr(usage, "prompt_tokens", None),
        completion_tokens=getattr(usage, "completion_tokens", None),
        total_tokens=getattr(usage, "total_tokens", None),
    )
