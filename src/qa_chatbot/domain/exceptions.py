"""Domain-specific errors."""


class DomainError(ValueError):
    """Base class for domain errors."""


class InvalidTeamIdError(DomainError):
    """Raised when a team identifier fails validation."""


class InvalidTimeWindowError(DomainError):
    """Raised when a time window is invalid or unsupported."""


class InvalidQAMetricsError(DomainError):
    """Raised when QA metrics are incomplete or invalid."""


class InvalidProjectStatusError(DomainError):
    """Raised when project status data is invalid."""


class InvalidDailyUpdateError(DomainError):
    """Raised when daily update data is invalid."""


class MissingSubmissionDataError(DomainError):
    """Raised when a submission has no meaningful data."""


class InvalidSubmissionTeamError(DomainError):
    """Raised when a submission references the wrong team."""


class LLMExtractionError(DomainError):
    """Raised when LLM extraction fails or returns invalid data."""


class AmbiguousExtractionError(LLMExtractionError):
    """Raised when LLM extraction returns ambiguous or missing data."""

    def __init__(self, label: str, *, is_missing: bool) -> None:
        """Initialize error message for ambiguous extraction."""
        message = f"Missing {label} in LLM response" if is_missing else f"Ambiguous {label} in LLM response"
        super().__init__(message)


class InvalidConfigurationError(DomainError):
    """Raised when application configuration is invalid."""


class DashboardRenderError(DomainError):
    """Raised when dashboard HTML rendering fails smoke checks."""
