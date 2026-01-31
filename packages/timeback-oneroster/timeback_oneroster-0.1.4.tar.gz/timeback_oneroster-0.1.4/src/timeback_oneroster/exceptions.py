"""
OneRoster Exceptions

Re-exports common errors and adds OneRoster-specific exceptions.
"""

from timeback_common import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    InputValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
    ValidationIssue,
    create_input_validation_error,
)

# OneRoster-specific base error (alias for TimebackError)
OneRosterError = TimebackError

__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "InputValidationError",
    "NotFoundError",
    "OneRosterError",
    "RateLimitError",
    "ServerError",
    "TimebackError",
    "ValidationError",
    "ValidationIssue",
    "create_input_validation_error",
]
