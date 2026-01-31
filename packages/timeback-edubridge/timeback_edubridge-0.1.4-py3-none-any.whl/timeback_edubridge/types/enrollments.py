"""
EduBridge Enrollment Types

Types for course-centric enrollment management.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .base import EnrollmentRole

# ═══════════════════════════════════════════════════════════════════════════════
# ENROLLMENT TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class EnrollmentPrimaryApp(BaseModel):
    """Primary application info within a course."""

    id: str
    name: str
    domains: list[str]


class EnrollmentCourse(BaseModel):
    """Course information within an enrollment."""

    id: str
    title: str
    metadata: dict[str, Any]
    subjects: list[str] | None = None
    grades: list[str] | None = None
    primary_app: EnrollmentPrimaryApp | None = Field(default=None, alias="primaryApp")

    model_config = ConfigDict(populate_by_name=True)


class EnrollmentSchool(BaseModel):
    """School information within an enrollment."""

    id: str
    name: str


class EnrollmentGoals(BaseModel):
    """Enrollment goals metadata."""

    daily_xp: int | None = Field(default=None, alias="dailyXp")
    daily_lessons: int | None = Field(default=None, alias="dailyLessons")
    daily_active_minutes: int | None = Field(default=None, alias="dailyActiveMinutes")
    daily_accuracy: int | None = Field(default=None, alias="dailyAccuracy")
    daily_mastered_units: int | None = Field(default=None, alias="dailyMasteredUnits")

    model_config = ConfigDict(populate_by_name=True)


class EnrollmentMetrics(BaseModel):
    """Enrollment metrics metadata."""

    total_xp: int | None = Field(default=None, alias="totalXp")
    total_lessons: int | None = Field(default=None, alias="totalLessons")
    total_grades: int | None = Field(default=None, alias="totalGrades")
    course_type: str | None = Field(default=None, alias="courseType")
    is_supplemental: bool | None = Field(default=None, alias="isSupplemental")

    model_config = ConfigDict(populate_by_name=True)


class EnrollmentMetadata(BaseModel):
    """Enrollment metadata."""

    goals: EnrollmentGoals | None = None
    metrics: EnrollmentMetrics | None = None

    model_config = ConfigDict(extra="allow")


class EnrollmentPeriod(BaseModel):
    """Period information for enrollments."""

    id: str
    title: str
    start_date: str | None = Field(default=None, alias="startDate")
    end_date: str | None = Field(default=None, alias="endDate")

    model_config = ConfigDict(populate_by_name=True)


class Enrollment(BaseModel):
    """A user's enrollment in a course."""

    id: str
    role: EnrollmentRole
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")
    metadata: EnrollmentMetadata | None = None
    course: EnrollmentCourse
    school: EnrollmentSchool
    periods: list[EnrollmentPeriod] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# REQUEST TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class EnrollOptions(BaseModel):
    """Options for enrolling a user in a course."""

    sourced_id: str | None = Field(default=None, alias="sourcedId")
    role: EnrollmentRole | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    metadata: EnrollmentMetadata | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# RESPONSE TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class ResetGoalsResult(BaseModel):
    """Response from reset goals operation."""

    updated: int
    errors: list[str]


class DefaultClassCourse(BaseModel):
    """Course info returned within a default class response."""

    id: str
    title: str
    metadata: dict[str, Any]

    model_config = ConfigDict(populate_by_name=True)


class DefaultClass(BaseModel):
    """
    Default class information for a course.

    Returned by the `/enrollments/defaultClass/:courseId/:schoolId?` endpoint.
    """

    id: str
    """Class sourcedId"""
    title: str
    """Class title"""
    class_code: str | None = Field(default=None, alias="classCode")
    """Class code (optional)"""
    subject_codes: list[str] = Field(alias="subjectCodes")
    """Subject codes"""
    subjects: list[str]
    """Subject names/objects"""
    grades: list[str] | None = None
    """Grade levels"""
    periods: list[str]
    """Academic period IDs"""
    course: DefaultClassCourse
    """Associated course"""

    model_config = ConfigDict(populate_by_name=True)
