"""
EduBridge Exceptions

Re-exports common errors and adds EduBridge-specific exceptions.
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

# EduBridge-specific base error (alias for TimebackError)
EdubridgeError = TimebackError

__all__ = [
    "APIError",
    "AuthenticationError",
    "EdubridgeError",
    "ForbiddenError",
    "InputValidationError",
    "NotFoundError",
    "RateLimitError",
    "ServerError",
    "TimebackError",
    "ValidationError",
    "ValidationIssue",
    "create_input_validation_error",
]
