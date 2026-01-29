"""
EduBridge Subject Track Types

Types for subject track management.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# SUBJECT TRACK TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class SubjectTrack(BaseModel):
    """A subject track mapping subject + grade to a target course."""

    id: str
    subject: str
    grade_level: str = Field(alias="gradeLevel")
    target_course_id: str = Field(alias="targetCourseId")
    target_course_name: str | None = Field(default=None, alias="targetCourseName")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SubjectTrackGroup(BaseModel):
    """A group of subject tracks."""

    id: str
    name: str
    description: str | None = None
    tracks: list[SubjectTrack]
    metadata: dict[str, Any] | None = None


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class SubjectTrackInput(BaseModel):
    """Parameters for creating/updating a subject track."""

    subject: str
    grade_level: str = Field(alias="gradeLevel")
    target_course_id: str = Field(alias="targetCourseId")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SubjectTrackUpsertInput(BaseModel):
    """
    Validated input for upserting a subject track.
    All fields must be non-empty strings, including the required id field.
    """

    id: str = Field(min_length=1)
    subject: str = Field(min_length=1)
    grade_level: str = Field(min_length=1, alias="gradeLevel")
    target_course_id: str = Field(min_length=1, alias="targetCourseId")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)
