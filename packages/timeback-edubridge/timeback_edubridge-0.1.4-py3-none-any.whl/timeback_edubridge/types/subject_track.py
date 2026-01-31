"""
EduBridge Subject Track Types

Types for subject track management.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# SUBJECT TRACK TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class SubjectTrackCourse(BaseModel):
    """A subject track course (subset of full course)."""

    sourced_id: str = Field(alias="sourcedId")
    title: str
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class SubjectTrackOrg(BaseModel):
    """A subject track org (school)."""

    sourced_id: str = Field(alias="sourcedId")
    name: str

    model_config = ConfigDict(populate_by_name=True)


class SubjectTrack(BaseModel):
    """
    A subject track mapping subject + grade to a target course.

    Response shape matches API: grade, course object, org.
    """

    id: str
    subject: str
    grade: str
    course: SubjectTrackCourse
    org: SubjectTrackOrg | None = None

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
    """
    Parameters for creating/updating a subject track.

    Field names match API: subject, grade, courseId.
    """

    subject: str
    grade: str
    course_id: str = Field(alias="courseId")
    org_sourced_id: str | None = Field(default=None, alias="orgSourcedId")

    model_config = ConfigDict(populate_by_name=True)


class SubjectTrackUpsertInput(BaseModel):
    """
    Validated input for upserting a subject track.

    The API generates the ID from the composite key (subject + grade + org),
    so no id field is needed in the input.
    """

    subject: str = Field(min_length=1)
    grade: str = Field(min_length=1)
    course_id: str = Field(min_length=1, alias="courseId")
    org_sourced_id: str | None = Field(default=None, alias="orgSourcedId")

    model_config = ConfigDict(populate_by_name=True)
