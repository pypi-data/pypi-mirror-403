"""
EduBridge Client-Side Validation Tests

These tests verify that validation happens BEFORE any network request is made.
This is important for:
- Fast failure on invalid input
- Avoiding unnecessary network round-trips
- Consistent error experience for SDK users
"""

from __future__ import annotations

from typing import Any

import pytest
from pydantic import ValidationError as PydanticValidationError

from timeback_common import EdubridgePaths, InputValidationError
from timeback_edubridge import SubjectTrackUpsertInput
from timeback_edubridge.resources.analytics import AnalyticsResource
from timeback_edubridge.resources.applications import ApplicationsResource
from timeback_edubridge.resources.enrollments import EnrollmentsResource
from timeback_edubridge.resources.learning_reports import LearningReportsResource
from timeback_edubridge.resources.subject_track import SubjectTrackResource
from timeback_edubridge.resources.users import UsersResource


class StubTransport:
    """
    Stub transport that tracks request count.

    Used to verify that validation fails BEFORE any network request is made.
    """

    def __init__(self) -> None:
        self.request_count = 0
        self.base_url = "https://example.test"
        self.paths = EdubridgePaths(base="/edubridge")

    async def request(
        self,
        _path: str,
        *,
        _params: dict[str, Any] | None = None,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        self.request_count += 1
        raise AssertionError("request should not be called - validation should have failed first")

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self.request(path, _params=params)

    async def post(self, path: str, body: Any) -> dict[str, Any]:
        return await self.request(path, _body=body)

    async def put(self, path: str, body: Any) -> dict[str, Any]:
        return await self.request(path, _body=body)

    async def delete(self, _path: str) -> None:
        self.request_count += 1
        raise AssertionError("request should not be called - validation should have failed first")


def create_stub_transport() -> StubTransport:
    """Create a new stub transport for testing."""
    return StubTransport()


class TestEdubridgeClientSideValidation:
    """
    Tests for client-side validation.
    """

    @pytest.mark.asyncio
    async def test_enrollments_list_validates_user_id_before_request(self) -> None:
        """enrollments.list validates userId before request."""
        transport = create_stub_transport()
        enrollments = EnrollmentsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await enrollments.list(user_id="")

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_enrollments_enroll_validates_ids_before_request(self) -> None:
        """enrollments.enroll validates ids before request."""
        transport = create_stub_transport()
        enrollments = EnrollmentsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await enrollments.enroll("", "course")

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_users_list_validates_roles_before_request(self) -> None:
        """users.list validates roles before request."""
        transport = create_stub_transport()
        users = UsersResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await users.list(roles=[])

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_analytics_get_activity_validates_email_student_id_before_request(self) -> None:
        """analytics.getActivity validates email/studentId before request."""
        transport = create_stub_transport()
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await analytics.get_activity(
                start_date="2025-01-01",
                end_date="2025-01-02",
            )

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_applications_get_metrics_validates_application_id_before_request(self) -> None:
        """applications.getMetrics validates application id before request."""
        transport = create_stub_transport()
        applications = ApplicationsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await applications.get_metrics("")

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_subject_tracks_upsert_validates_input_before_request(self) -> None:
        """subjectTracks.upsert validates input before request."""

        transport = create_stub_transport()
        subject_tracks = SubjectTrackResource(transport)  # type: ignore[arg-type]

        # Empty subject should fail validation (either via Pydantic or InputValidationError)
        # Pydantic validates at model construction time with min_length constraints
        with pytest.raises((InputValidationError, PydanticValidationError)):
            await subject_tracks.upsert(
                SubjectTrackUpsertInput(
                    subject="",  # Empty subject should fail validation
                    grade="9",
                    course_id="course-1",
                )
            )

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_learning_reports_get_map_profile_validates_user_id_before_request(self) -> None:
        """learningReports.getMapProfile validates userId before request."""
        transport = create_stub_transport()
        learning_reports = LearningReportsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await learning_reports.get_map_profile("")

        assert transport.request_count == 0

    @pytest.mark.asyncio
    async def test_learning_reports_get_time_saved_validates_user_id_before_request(self) -> None:
        """learningReports.getTimeSaved validates userId before request."""
        transport = create_stub_transport()
        learning_reports = LearningReportsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError):
            await learning_reports.get_time_saved("")

        assert transport.request_count == 0


class TestEdubridgeValidationErrorMessages:
    """
    Tests for validation error message quality.

    These tests ensure that error messages are helpful and include proper context.
    """

    @pytest.mark.asyncio
    async def test_validation_error_includes_field_path(self) -> None:
        """Validation errors should include the field path."""
        transport = create_stub_transport()
        users = UsersResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError) as exc_info:
            await users.list(roles=[])

        error = exc_info.value
        assert len(error.issues) > 0
        assert any("roles" in issue.path for issue in error.issues)

    @pytest.mark.asyncio
    async def test_validation_error_for_empty_string(self) -> None:
        """Empty string validation should have clear message."""
        transport = create_stub_transport()
        enrollments = EnrollmentsResource(transport)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError) as exc_info:
            await enrollments.list(user_id="")

        error = exc_info.value
        assert "user_id" in str(error)
