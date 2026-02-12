"""Extraction confidence value object."""

from __future__ import annotations

from dataclasses import dataclass

from qa_chatbot.domain.exceptions import InvalidConfigurationError

_ALLOWED_CONFIDENCE_LEVELS = {"high", "medium", "low"}


@dataclass(frozen=True)
class ExtractionConfidence:
    """Normalized confidence level for LLM extraction outputs."""

    value: str

    def __post_init__(self) -> None:
        """Validate and normalize confidence value."""
        normalized = self.value.strip().lower()
        if normalized not in _ALLOWED_CONFIDENCE_LEVELS:
            msg = "Confidence must be one of: high, medium, low"
            raise InvalidConfigurationError(msg)
        object.__setattr__(self, "value", normalized)

    @classmethod
    def from_raw(cls, value: str) -> ExtractionConfidence:
        """Create confidence from adapter-provided raw value."""
        return cls(value=value)

    @classmethod
    def low(cls) -> ExtractionConfidence:
        """Return low confidence value."""
        return cls(value="low")

    @property
    def is_high(self) -> bool:
        """Return whether confidence is high."""
        return self.value == "high"
