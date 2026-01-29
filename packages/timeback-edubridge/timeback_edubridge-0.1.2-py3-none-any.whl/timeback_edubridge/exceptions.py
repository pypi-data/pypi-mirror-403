"""
EduBridge Exceptions

Re-exports common errors and adds EduBridge-specific exceptions.
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

# EduBridge-specific base error (alias for TimebackError)
EdubridgeError = TimebackError

__all__ = [
    "APIError",
    "AuthenticationError",
    "EdubridgeError",
    "ForbiddenError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "ValidationError",
]
