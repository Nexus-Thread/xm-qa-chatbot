"""Backward-compatible imports for OpenAI transport helpers."""

from .constants import DEFAULT_TIMEOUT_SECONDS, DEFAULT_VERIFY_SSL
from .factory import build_client, build_http_client
from .protocols import OpenAIClientProtocol
from .transport import OpenAIClient

__all__ = [
    "DEFAULT_TIMEOUT_SECONDS",
    "DEFAULT_VERIFY_SSL",
    "OpenAIClient",
    "OpenAIClientProtocol",
    "build_client",
    "build_http_client",
]
