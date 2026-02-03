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
