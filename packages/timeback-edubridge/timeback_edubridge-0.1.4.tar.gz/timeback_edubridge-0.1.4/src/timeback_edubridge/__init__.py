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

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("timeback-edubridge")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .client import EdubridgeClient
from .exceptions import (
    APIError,
    AuthenticationError,
    EdubridgeError,
    ForbiddenError,
    InputValidationError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimebackError,
    ValidationError,
    ValidationIssue,
    create_input_validation_error,
)
from .types import (
    ActivityMetricsData,
    AggregatedMetrics,
    Application,
    ApplicationMetrics,
    DailyActivityMap,
    DataResponse,
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
    MapProfile,
    PrimaryOrg,
    ResetGoalsResult,
    Role,
    Status,
    SubjectMetrics,
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
    "APIError",
    "ActivityMetricsData",
    "AggregatedMetrics",
    "Application",
    "ApplicationMetrics",
    "AuthenticationError",
    "DailyActivityMap",
    "DataResponse",
    "DefaultClass",
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
    "InputValidationError",
    "MapProfile",
    "NotFoundError",
    "PrimaryOrg",
    "RateLimitError",
    "ResetGoalsResult",
    "Role",
    "ServerError",
    "Status",
    "SubjectMetrics",
    "SubjectTrack",
    "SubjectTrackGroup",
    "SubjectTrackInput",
    "SubjectTrackUpsertInput",
    "TimeSaved",
    "TimeSpentMetricsData",
    "TimebackError",
    "User",
    "UserApp",
    "UserCredential",
    "UserId",
    "UserProfile",
    "UserRole",
    "ValidationError",
    "ValidationIssue",
    "WeeklyFactRecord",
    "WeeklyFacts",
    "__version__",
    "aggregate_activity_metrics",
    "create_input_validation_error",
    "normalize_boolean",
    "normalize_date",
    "normalize_user",
]
