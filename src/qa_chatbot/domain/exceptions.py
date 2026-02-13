"""Domain-specific errors."""


class DomainError(ValueError):
    """Base class for domain errors."""


class InvalidProjectIdError(DomainError):
    """Raised when a project identifier fails validation."""


class InvalidStreamIdError(DomainError):
    """Raised when a stream identifier fails validation."""


class InvalidTimeWindowError(DomainError):
    """Raised when a time window is invalid or unsupported."""


class MissingSubmissionDataError(DomainError):
    """Raised when a submission has no meaningful data."""


class InvalidSubmissionTeamError(DomainError):
    """Raised when a submission references the wrong team."""


class InvalidConfigurationError(DomainError):
    """Raised when application configuration is invalid."""
