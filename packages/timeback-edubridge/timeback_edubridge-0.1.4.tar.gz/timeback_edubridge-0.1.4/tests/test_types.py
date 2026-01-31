"""
Tests for EduBridge types.
"""

from timeback_edubridge import (
    Application,
    DefaultClass,
    Enrollment,
    HighestGradeMastered,
    MapProfile,
    SubjectTrack,
    TimeSaved,
    User,
)


class TestEnrollmentTypes:
    """Tests for enrollment types."""

    def test_enrollment_parsing(self) -> None:
        """Enrollment should parse from API response."""
        data = {
            "id": "enroll-123",
            "role": "student",
            "beginDate": "2025-01-01",
            "endDate": "2025-06-30",
            "course": {
                "id": "course-456",
                "title": "Algebra 1",
                "metadata": {},
            },
            "school": {
                "id": "school-789",
                "name": "Test School",
            },
        }

        enrollment = Enrollment(**data)

        assert enrollment.id == "enroll-123"
        assert enrollment.role == "student"
        assert enrollment.begin_date == "2025-01-01"
        assert enrollment.end_date == "2025-06-30"
        assert enrollment.course.id == "course-456"
        assert enrollment.course.title == "Algebra 1"
        assert enrollment.school.id == "school-789"
        assert enrollment.school.name == "Test School"

    def test_default_class_parsing(self) -> None:
        """DefaultClass should parse from API response."""
        data = {
            "id": "class-123",
            "title": "Default Class",
            "classCode": "DC-001",
            "subjectCodes": ["MATH"],
            "subjects": ["Mathematics"],
            "grades": ["9"],
            "periods": ["term-456"],
            "course": {
                "id": "course-789",
                "title": "Algebra 1",
                "metadata": {},
            },
        }

        default_class = DefaultClass(**data)

        assert default_class.id == "class-123"
        assert default_class.title == "Default Class"
        assert default_class.class_code == "DC-001"
        assert default_class.subject_codes == ["MATH"]
        assert default_class.subjects == ["Mathematics"]
        assert default_class.grades == ["9"]
        assert default_class.periods == ["term-456"]
        assert default_class.course.id == "course-789"
        assert default_class.course.title == "Algebra 1"


class TestUserTypes:
    """Tests for user types."""

    def test_user_parsing(self) -> None:
        """User should parse from API response."""
        data = {
            "sourcedId": "user-123",
            "status": "active",
            "dateLastModified": "2025-01-01T00:00:00Z",
            "userIds": [{"type": "email", "identifier": "test@example.com"}],
            "enabledUser": "true",
            "givenName": "John",
            "familyName": "Doe",
            "roles": [],
            "agents": [],
            "userProfiles": [],
        }

        user = User(**data)

        assert user.sourced_id == "user-123"
        assert user.status == "active"
        assert user.given_name == "John"
        assert user.family_name == "Doe"
        assert user.enabled_user == "true"
        assert len(user.user_ids) == 1
        assert user.user_ids[0].type == "email"


class TestAnalyticsTypes:
    """Tests for analytics types."""

    def test_highest_grade_mastered_parsing(self) -> None:
        """HighestGradeMastered should parse from API response."""
        data = {
            "studentId": "student-123",
            "subject": "Math",
            "grades": {
                "ritGrade": 220,
                "edulasticGrade": "8",
                "placementGrade": "7",
                "testOutGrade": None,
                "highestGradeOverall": "8",
            },
        }

        result = HighestGradeMastered(**data)

        assert result.student_id == "student-123"
        assert result.subject == "Math"
        assert result.grades.rit_grade == 220
        assert result.grades.edulastic_grade == "8"
        assert result.grades.highest_grade_overall == "8"


class TestApplicationTypes:
    """Tests for application types."""

    def test_application_parsing(self) -> None:
        """Application should parse from API response."""
        data = {
            "sourcedId": "app-123",
            "name": "Math Academy",
            "description": "Interactive math learning",
            "domain": ["mathacademy.com", "app.mathacademy.com"],
        }

        app = Application(**data)

        assert app.sourced_id == "app-123"
        assert app.name == "Math Academy"
        assert app.description == "Interactive math learning"
        assert len(app.domain) == 2


class TestSubjectTrackTypes:
    """Tests for subject track types."""

    def test_subject_track_parsing(self) -> None:
        """SubjectTrack should parse from API response."""
        data = {
            "id": "track-123",
            "subject": "Math",
            "grade": "9",
            "course": {
                "sourcedId": "course-456",
                "title": "Algebra 1",
                "metadata": None,
            },
            "org": {
                "sourcedId": "school-789",
                "name": "Test School",
            },
        }

        track = SubjectTrack(**data)

        assert track.id == "track-123"
        assert track.subject == "Math"
        assert track.grade == "9"
        assert track.course.sourced_id == "course-456"
        assert track.course.title == "Algebra 1"
        assert track.org is not None
        assert track.org.sourced_id == "school-789"
        assert track.org.name == "Test School"


class TestLearningReportTypes:
    """Tests for learning report types."""

    def test_map_profile_parsing(self) -> None:
        """MapProfile should parse from API response."""
        data = {
            "userId": "user-123",
            "ritScore": 220,
            "percentile": 75,
            "gradeLevel": "8",
            "testDate": "2025-01-15",
            "subject": "Math",
        }

        profile = MapProfile(**data)

        assert profile.user_id == "user-123"
        assert profile.rit_score == 220
        assert profile.percentile == 75
        assert profile.grade_level == "8"

    def test_time_saved_parsing(self) -> None:
        """TimeSaved should parse from API response."""
        data = {
            "totalHoursSaved": 5,
            "totalDaysSaved": 0.625,
            "schoolDaysElapsed": 100,
            "earliestStartDate": "2024-08-01",
            "schoolYearStartDate": "2024-08-15",
            "calculation": {"description": "test calculation"},
        }

        time_saved = TimeSaved(**data)

        assert time_saved.total_hours_saved == 5
        assert time_saved.total_days_saved == 0.625
        assert time_saved.school_days_elapsed == 100
        assert time_saved.earliest_start_date == "2024-08-01"
        assert time_saved.school_year_start_date == "2024-08-15"
        assert time_saved.calculation is not None
