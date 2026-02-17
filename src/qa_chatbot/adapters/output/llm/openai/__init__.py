"""OpenAI-based LLM adapter."""

from .adapter import OpenAIAdapter, OpenAISettings
from .client import OpenAIClient, OpenAIClientProtocol, build_client, build_http_client
from .exceptions import AmbiguousExtractionError, InvalidHistoryError, LLMExtractionError
from .schemas import ProjectIdSchema, TestCoverageSchema, TimeWindowSchema

__all__ = [
    "AmbiguousExtractionError",
    "InvalidHistoryError",
    "LLMExtractionError",
    "OpenAIAdapter",
    "OpenAIClient",
    "OpenAIClientProtocol",
    "OpenAISettings",
    "ProjectIdSchema",
    "TestCoverageSchema",
    "TimeWindowSchema",
    "build_client",
    "build_http_client",
]
