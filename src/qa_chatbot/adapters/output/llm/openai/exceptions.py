"""OpenAI adapter-specific errors."""

from qa_chatbot.domain.exceptions import DomainError


class LLMExtractionError(DomainError):
    """Raised when LLM extraction fails or returns invalid data."""


class AmbiguousExtractionError(LLMExtractionError):
    """Raised when LLM extraction returns ambiguous or missing data."""

    def __init__(self, label: str, *, is_missing: bool) -> None:
        """Initialize error message for ambiguous extraction."""
        message = f"Missing {label} in LLM response" if is_missing else f"Ambiguous {label} in LLM response"
        super().__init__(message)


class InvalidHistoryError(LLMExtractionError):
    """Raised when conversation history payload is invalid."""
