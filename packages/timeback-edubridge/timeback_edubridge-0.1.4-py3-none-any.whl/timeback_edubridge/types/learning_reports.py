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

    user_id: str | None = Field(default=None, alias="userId")
    rit_score: int | None = Field(default=None, alias="ritScore")
    percentile: int | None = None
    grade_level: str | None = Field(default=None, alias="gradeLevel")
    test_date: str | None = Field(default=None, alias="testDate")
    subject: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")


# ═══════════════════════════════════════════════════════════════════════════════
# TIME SAVED TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class TimeSavedCalculation(BaseModel):
    """Time saved calculation details."""

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TimeSaved(BaseModel):
    """Time saved metrics for a user."""

    total_hours_saved: float | int | None = Field(default=None, alias="totalHoursSaved")
    total_days_saved: float | int | None = Field(default=None, alias="totalDaysSaved")
    school_days_elapsed: int | None = Field(default=None, alias="schoolDaysElapsed")
    earliest_start_date: str | None = Field(default=None, alias="earliestStartDate")
    school_year_start_date: str | None = Field(default=None, alias="schoolYearStartDate")
    calculation: TimeSavedCalculation | dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
