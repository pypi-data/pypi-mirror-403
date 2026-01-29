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
    """Reference to another entity."""

    href: str
    sourced_id: str
    type: str

    model_config = ConfigDict(populate_by_name=True, alias_generator=lambda s: s)


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE WRAPPERS
# ═══════════════════════════════════════════════════════════════════════════════

T = TypeVar("T")


class DataResponse[T](BaseModel):
    """Standard EduBridge API response wrapper."""

    data: T
