# Timeback EduBridge Client

Python client for the Timeback EduBridge API with async support.

## Installation

```bash
# pip
pip install timeback-edubridge

# uv (add to a project)
uv add timeback-edubridge

# uv (install into current environment)
uv pip install timeback-edubridge
```

## Quick Start

```python
from timeback_edubridge import EdubridgeClient

# Initialize with explicit configuration
client = EdubridgeClient(
    base_url="https://api.timeback.ai",
    auth_url="https://auth.timeback.ai/oauth2/token",
    client_id="your-client-id",
    client_secret="your-client-secret",
)

# Or use environment variables with a prefix
client = EdubridgeClient(env="PRODUCTION")
# Reads: PRODUCTION_EDUBRIDGE_BASE_URL, PRODUCTION_EDUBRIDGE_TOKEN_URL, etc.
```

## Resources

### Enrollments

```python
# List enrollments for a user
enrollments = await client.enrollments.list(user_id="user-123")

# Enroll a user in a course
enrollment = await client.enrollments.enroll(
    user_id="user-123",
    course_id="course-456",
    school_id="school-789",  # Optional
)

# Unenroll a user
await client.enrollments.unenroll(
    user_id="user-123",
    course_id="course-456",
)

# Reset goals for a course
result = await client.enrollments.reset_goals("course-456")

# Reset a user's progress
await client.enrollments.reset_progress("user-123", "course-456")

# Get default class for a course
default_class = await client.enrollments.get_default_class("course-456")
```

### Users

```python
# List users by role
users = await client.users.list(roles=["student", "teacher"])

# Convenience methods
students = await client.users.list_students()
teachers = await client.users.list_teachers()

# Search users
results = await client.users.search(
    roles=["student"],
    search="john",
    limit=50,
)

# With additional filters
filtered = await client.users.list(
    roles=["student"],
    org_sourced_ids=["school-123"],
    limit=100,
    offset=0,
)
```

### Analytics

```python
# Get activity for a date range
activity = await client.analytics.get_activity(
    student_id="student-123",  # or email="student@example.com"
    start_date="2025-01-01",
    end_date="2025-01-31",
    timezone="America/New_York",
)

# Get weekly facts
facts = await client.analytics.get_weekly_facts(
    student_id="student-123",
    week_date="2025-01-15",
)

# Get enrollment-specific facts
enrollment_facts = await client.analytics.get_enrollment_facts(
    enrollment_id="enrollment-123",
    start_date="2025-01-01",
    end_date="2025-01-31",
)

# Get highest grade mastered
grade = await client.analytics.get_highest_grade_mastered(
    student_id="student-123",
    subject="Math",
)
```

### Applications

```python
# List all applications
apps = await client.applications.list()

# Get metrics for an application
metrics = await client.applications.get_metrics("app-123")
```

### Subject Tracks

```python
from timeback_edubridge import SubjectTrackInput

# List all subject tracks
tracks = await client.subject_tracks.list()

# Create or update a subject track
track = await client.subject_tracks.upsert(
    id="track-123",
    data=SubjectTrackInput(
        subject="Math",
        grade_level="9",
        target_course_id="course-456",
    ),
)

# Delete a subject track
await client.subject_tracks.delete("track-123")

# List subject track groups
groups = await client.subject_tracks.list_groups()
```

### Learning Reports

```python
# Get MAP profile for a user
profile = await client.learning_reports.get_map_profile("user-123")

# Get time saved metrics
time_saved = await client.learning_reports.get_time_saved("user-123")
```

## Context Manager

The client can be used as an async context manager:

```python
async with EdubridgeClient(base_url="...") as client:
    enrollments = await client.enrollments.list(user_id="user-123")
# Client is automatically closed
```

## Error Handling

```python
from timeback_edubridge import (
    EdubridgeError,
    AuthenticationError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
    APIError,
)

try:
    enrollments = await client.enrollments.list(user_id="user-123")
except AuthenticationError:
    print("Invalid credentials")
except ForbiddenError:
    print("Access denied")
except NotFoundError:
    print("Resource not found")
except ValidationError as e:
    print(f"Invalid request: {e}")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

## Environment Variables

When using `env` parameter, the client looks for these variables:

| Variable | Description |
|----------|-------------|
| `{PREFIX}_EDUBRIDGE_BASE_URL` | Base URL for the API |
| `{PREFIX}_EDUBRIDGE_TOKEN_URL` | OAuth2 token endpoint |
| `{PREFIX}_EDUBRIDGE_CLIENT_ID` | OAuth2 client ID |
| `{PREFIX}_EDUBRIDGE_CLIENT_SECRET` | OAuth2 client secret |

Without a prefix, it uses the variables without the prefix (e.g., `EDUBRIDGE_BASE_URL`).
