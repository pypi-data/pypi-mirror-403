"""Custom exceptions for EntelligenceAI CLI."""


class EntelligenceError(Exception):
    """Base exception for EntelligenceAI CLI errors."""

    pass


class AuthenticationError(EntelligenceError):
    """Authentication-related errors."""

    pass


class APIError(EntelligenceError):
    """API-related errors."""

    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


class GitError(EntelligenceError):
    """Git operation errors."""

    pass


class ValidationError(EntelligenceError):
    """Input validation errors."""

    pass


class ConfigurationError(EntelligenceError):
    """Configuration-related errors."""

    pass


class ReviewError(EntelligenceError):
    """Code review operation errors."""

    pass
