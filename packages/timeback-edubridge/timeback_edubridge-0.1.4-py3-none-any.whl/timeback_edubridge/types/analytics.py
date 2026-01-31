"""
EduBridge Analytics Types

Types for analytics and reporting endpoints.
"""

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# CORE METRICS TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class ActivityMetricsData(BaseModel):
    """Activity metrics from the API."""

    xp_earned: float = Field(alias="xpEarned")
    total_questions: int = Field(alias="totalQuestions")
    correct_questions: int = Field(alias="correctQuestions")
    mastered_units: int = Field(alias="masteredUnits")

    model_config = ConfigDict(populate_by_name=True)


class TimeSpentMetricsData(BaseModel):
    """Time spent metrics from the API."""

    active_seconds: float = Field(alias="activeSeconds")
    inactive_seconds: float = Field(alias="inactiveSeconds")
    waste_seconds: float = Field(alias="wasteSeconds")

    model_config = ConfigDict(populate_by_name=True)


class SubjectMetrics(BaseModel):
    """Metrics for a specific subject on a given day."""

    activity_metrics: ActivityMetricsData = Field(alias="activityMetrics")
    time_spent_metrics: TimeSpentMetricsData = Field(alias="timeSpentMetrics")
    apps: list[str]

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# ACTIVITY RESPONSE TYPES
# ═══════════════════════════════════════════════════════════════════════════════

# Activity data grouped by date, then by subject
# Example: {"2025-12-17": {"FastMath": SubjectMetrics}}
DailyActivityMap = dict[str, dict[str, SubjectMetrics]]

# Enrollment facts has the same structure
EnrollmentFacts = DailyActivityMap


# ═══════════════════════════════════════════════════════════════════════════════
# WEEKLY FACTS TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class WeeklyFactRecord(BaseModel):
    """A single fact/event record from the weekly facts endpoint."""

    id: int
    email: str
    date: str
    datetime: str
    username: str | None = None
    user_grade: str | None = Field(default=None, alias="userGrade")
    user_family_name: str | None = Field(default=None, alias="userFamilyName")
    user_given_name: str | None = Field(default=None, alias="userGivenName")
    user_id: str | None = Field(default=None, alias="userId")
    subject: str | None = None
    app: str | None = None
    course_id: str | None = Field(default=None, alias="courseId")
    course_name: str | None = Field(default=None, alias="courseName")
    campus_id: str | None = Field(default=None, alias="campusId")
    campus_name: str | None = Field(default=None, alias="campusName")
    enrollment_id: str | None = Field(default=None, alias="enrollmentId")
    activity_id: str | None = Field(default=None, alias="activityId")
    activity_name: str | None = Field(default=None, alias="activityName")
    total_questions: int | None = Field(default=None, alias="totalQuestions")
    correct_questions: int | None = Field(default=None, alias="correctQuestions")
    xp_earned: float | None = Field(default=None, alias="xpEarned")
    mastered_units: int | None = Field(default=None, alias="masteredUnits")
    active_seconds: str | None = Field(default=None, alias="activeSeconds")
    inactive_seconds: str | None = Field(default=None, alias="inactiveSeconds")
    waste_seconds: str | None = Field(default=None, alias="wasteSeconds")
    source: str
    alpha_level: str | None = Field(default=None, alias="alphaLevel")
    generated_at: str | None = Field(default=None, alias="generatedAt")
    send_time: str | None = Field(default=None, alias="sendTime")
    sensor: str | None = None
    event_type: str | None = Field(default=None, alias="eventType")
    year: int
    month: int
    day: int
    day_of_week: int = Field(alias="dayOfWeek")

    model_config = ConfigDict(populate_by_name=True)


# Weekly facts is a list of individual fact records
WeeklyFacts = list[WeeklyFactRecord]


# ═══════════════════════════════════════════════════════════════════════════════
# HIGHEST GRADE TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class GradeMasteryData(BaseModel):
    """Grade mastery data from various sources."""

    rit_grade: int | None = Field(default=None, alias="ritGrade")
    edulastic_grade: str | None = Field(default=None, alias="edulasticGrade")
    placement_grade: str | None = Field(default=None, alias="placementGrade")
    test_out_grade: str | None = Field(default=None, alias="testOutGrade")
    highest_grade_overall: str | None = Field(default=None, alias="highestGradeOverall")

    model_config = ConfigDict(populate_by_name=True)


class HighestGradeMastered(BaseModel):
    """Highest grade mastered for a subject."""

    student_id: str = Field(alias="studentId")
    subject: str
    grades: GradeMasteryData

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# AGGREGATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


class AggregatedMetrics(BaseModel):
    """Aggregated metrics across all dates and subjects."""

    total_xp: float = Field(alias="totalXp")
    total_questions: int = Field(alias="totalQuestions")
    correct_questions: int = Field(alias="correctQuestions")
    mastered_units: int = Field(alias="masteredUnits")
    active_seconds: float = Field(alias="activeSeconds")
    inactive_seconds: float = Field(alias="inactiveSeconds")
    waste_seconds: float = Field(alias="wasteSeconds")
    day_count: int = Field(alias="dayCount")
    subject_count: int = Field(alias="subjectCount")

    model_config = ConfigDict(populate_by_name=True)
