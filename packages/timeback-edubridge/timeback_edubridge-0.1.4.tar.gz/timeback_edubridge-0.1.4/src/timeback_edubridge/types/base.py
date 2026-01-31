"""
EduBridge Base Types

Common types shared across EduBridge resources.
"""

from typing import Literal, TypeVar

from pydantic import BaseModel, ConfigDict

# ═══════════════════════════════════════════════════════════════════════════════
# COMMON TYPES
# ═══════════════════════════════════════════════════════════════════════════════

Status = Literal["active", "tobedeleted"]

Role = Literal[
    "administrator",
    "aide",
    "guardian",
    "parent",
    "proctor",
    "relative",
    "student",
    "teacher",
]

EnrollmentRole = Literal["administrator", "proctor", "student", "teacher"]


class GUIDRef(BaseModel):
    """
    Full reference to another entity, including the sourcedId.

    Use this when the API returns the complete reference with sourcedId.
    """

    href: str
    sourced_id: str
    type: str

    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda s: s)


class GUIDRefBase(BaseModel):
    """
    Base reference with minimal fields.

    Some API responses (e.g., user role orgs) only return `href` and `type`
    without the `sourcedId`. Use this type for those contexts.
    """

    href: str
    type: str

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════════

T = TypeVar("T")


class DataResponse[T](BaseModel):
    """Standard EduBridge API response wrapper."""

    data: T
