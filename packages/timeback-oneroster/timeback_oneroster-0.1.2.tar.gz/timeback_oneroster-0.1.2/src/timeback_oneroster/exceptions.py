"""
OneRoster Exceptions

Re-exports common errors and adds OneRoster-specific exceptions.
"""

from timeback_common import (
    APIError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
)

# OneRoster-specific base error (alias for TimebackError)
OneRosterError = TimebackError

__all__ = [
    "APIError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "OneRosterError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
]
