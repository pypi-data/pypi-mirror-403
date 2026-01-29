"""
EduBridge Types

Type definitions for the EduBridge client.
"""

from .analytics import (
    ActivityMetricsData,
    AggregatedMetrics,
    DailyActivityMap,
    EnrollmentFacts,
    GradeMasteryData,
    HighestGradeMastered,
    SubjectMetrics,
    TimeSpentMetricsData,
    WeeklyFactRecord,
    WeeklyFacts,
)
from .applications import Application, ApplicationMetrics
from .base import DataResponse, EnrollmentRole, GUIDRef, Role, Status
from .enrollments import (
    DefaultClass,
    Enrollment,
    EnrollmentCourse,
    EnrollmentGoals,
    EnrollmentMetadata,
    EnrollmentMetrics,
    EnrollmentPeriod,
    EnrollmentPrimaryApp,
    EnrollmentSchool,
    EnrollOptions,
    ResetGoalsResult,
)
from .learning_reports import MapProfile, TimeSaved
from .subject_track import (
    SubjectTrack,
    SubjectTrackGroup,
    SubjectTrackInput,
    SubjectTrackUpsertInput,
)
from .users import (
    PrimaryOrg,
    User,
    UserApp,
    UserCredential,
    UserId,
    UserProfile,
    UserRole,
)

__all__ = [
    "ActivityMetricsData",
    "AggregatedMetrics",
    "Application",
    "ApplicationMetrics",
    "DailyActivityMap",
    "DataResponse",
    "DefaultClass",
    "EnrollOptions",
    "Enrollment",
    "EnrollmentCourse",
    "EnrollmentFacts",
    "EnrollmentGoals",
    "EnrollmentMetadata",
    "EnrollmentMetrics",
    "EnrollmentPeriod",
    "EnrollmentPrimaryApp",
    "EnrollmentRole",
    "EnrollmentSchool",
    "GUIDRef",
    "GradeMasteryData",
    "HighestGradeMastered",
    "MapProfile",
    "PrimaryOrg",
    "ResetGoalsResult",
    "Role",
    "Status",
    "SubjectMetrics",
    "SubjectTrack",
    "SubjectTrackGroup",
    "SubjectTrackInput",
    "SubjectTrackUpsertInput",
    "TimeSaved",
    "TimeSpentMetricsData",
    "User",
    "UserApp",
    "UserCredential",
    "UserId",
    "UserProfile",
    "UserRole",
    "WeeklyFactRecord",
    "WeeklyFacts",
]
