"""Dashboard adapter-specific errors."""

from qa_chatbot.domain import DomainError


class DashboardRenderError(DomainError):
    """Raised when dashboard rendering fails smoke checks."""
