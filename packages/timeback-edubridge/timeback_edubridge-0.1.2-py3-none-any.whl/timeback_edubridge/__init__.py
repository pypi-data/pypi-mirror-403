"""
Timeback EduBridge Client

A Python client for the Timeback EduBridge API with async support.

Example:
    ```python
    from timeback_edubridge import EdubridgeClient

    client = EdubridgeClient(
        base_url="https://api.example.com",
        auth_url="https://auth.example.com/oauth2/token",
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # List enrollments for a user
    enrollments = await client.enrollments.list(user_id="user-123")

    # Get analytics
    activity = await client.analytics.get_activity(
        student_id="student-123",
        start_date="2025-01-01",
        end_date="2025-01-31",
    )
    ```
"""

from .client import EdubridgeClient
from .exceptions import (
    APIError,
    AuthenticationError,
    EdubridgeError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from .types import (
    # Analytics
    ActivityMetricsData,
    AggregatedMetrics,
    # Applications
    Application,
    ApplicationMetrics,
    DailyActivityMap,
    # Base
    DataResponse,
    # Enrollments
    DefaultClass,
    Enrollment,
    EnrollmentCourse,
    EnrollmentFacts,
    EnrollmentGoals,
    EnrollmentMetadata,
    EnrollmentMetrics,
    EnrollmentPeriod,
    EnrollmentPrimaryApp,
    EnrollmentRole,
    EnrollmentSchool,
    EnrollOptions,
    GradeMasteryData,
    GUIDRef,
    HighestGradeMastered,
    # Learning Reports
    MapProfile,
    # Users
    PrimaryOrg,
    ResetGoalsResult,
    Role,
    Status,
    SubjectMetrics,
    # Subject Track
    SubjectTrack,
    SubjectTrackGroup,
    SubjectTrackInput,
    SubjectTrackUpsertInput,
    TimeSaved,
    TimeSpentMetricsData,
    User,
    UserApp,
    UserCredential,
    UserId,
    UserProfile,
    UserRole,
    WeeklyFactRecord,
    WeeklyFacts,
)
from .utils import (
    aggregate_activity_metrics,
    normalize_boolean,
    normalize_date,
    normalize_user,
)

__all__ = [
    # Exceptions
    "APIError",
    # Analytics
    "ActivityMetricsData",
    "AggregatedMetrics",
    # Applications
    "Application",
    "ApplicationMetrics",
    "AuthenticationError",
    "DailyActivityMap",
    # Base
    "DataResponse",
    # Enrollments
    "DefaultClass",
    # Client
    "EdubridgeClient",
    "EdubridgeError",
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
    "ForbiddenError",
    "GUIDRef",
    "GradeMasteryData",
    "HighestGradeMastered",
    # Learning Reports
    "MapProfile",
    "NotFoundError",
    # Users
    "PrimaryOrg",
    "ResetGoalsResult",
    "Role",
    "Status",
    "SubjectMetrics",
    # Subject Track
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
    "ValidationError",
    "WeeklyFactRecord",
    "WeeklyFacts",
    # Utilities
    "aggregate_activity_metrics",
    "normalize_boolean",
    "normalize_date",
    "normalize_user",
]
