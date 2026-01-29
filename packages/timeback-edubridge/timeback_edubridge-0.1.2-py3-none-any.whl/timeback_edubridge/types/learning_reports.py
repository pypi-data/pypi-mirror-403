"""
EduBridge Learning Reports Types

Types for learning reports endpoints.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# MAP PROFILE TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class MapProfile(BaseModel):
    """MAP (Measures of Academic Progress) profile data."""

    user_id: str = Field(alias="userId")
    rit_score: int | None = Field(default=None, alias="ritScore")
    percentile: int | None = None
    grade_level: str | None = Field(default=None, alias="gradeLevel")
    test_date: str | None = Field(default=None, alias="testDate")
    subject: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TIME SAVED TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class TimeSaved(BaseModel):
    """Time saved metrics for a user."""

    user_id: str = Field(alias="userId")
    total_minutes_saved: int | None = Field(default=None, alias="totalMinutesSaved")
    breakdown_by_subject: dict[str, int] | None = Field(default=None, alias="breakdownBySubject")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)
