"""
Enrollments Resource

Simplified, course-centric enrollment management.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

from timeback_common import validate_non_empty_string

from ..types import DefaultClass, Enrollment, EnrollOptions, ResetGoalsResult

if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.enrollments")


class EnrollmentsResource:
    """
    Enrollments resource for course-centric enrollment management.

    Provides simplified methods to enroll/unenroll users in courses
    without needing to understand the underlying OneRoster academic hierarchy.

    Example:
        ```python
        # List enrollments for a user
        enrollments = await client.enrollments.list(user_id="user-123")

        # Enroll a user in a course
        enrollment = await client.enrollments.enroll(
            user_id="user-123",
            course_id="course-456",
        )

        # Unenroll a user from a course
        await client.enrollments.unenroll(
            user_id="user-123",
            course_id="course-456",
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def list(self, *, user_id: str) -> list[Enrollment]:
        """
        List enrollments for a user.

        Args:
            user_id: User ID to filter enrollments by

        Returns:
            List of course enrollments

        Raises:
            InputValidationError: If user_id is empty
        """
        validate_non_empty_string(user_id, "user_id")

        log.debug("list", extra={"user_id": user_id})
        path = f"{self._transport.paths.base}/enrollments/user/{quote(user_id)}"
        response = await self._transport.get(path)
        return [Enrollment(**e) for e in response.get("data", [])]

    async def enroll(
        self,
        user_id: str,
        course_id: str,
        school_id: str | None = None,
        options: EnrollOptions | None = None,
    ) -> Enrollment:
        """
        Enroll a user in a course.

        Automatically handles creating the appropriate class and academic session
        records required by OneRoster.

        Args:
            user_id: User ID to enroll
            course_id: Course ID to enroll in
            school_id: Optional school ID (uses user's primary org if not specified)
            options: Enrollment options (role, metadata, etc.)

        Returns:
            Created enrollment

        Raises:
            InputValidationError: If user_id or course_id is empty
        """
        validate_non_empty_string(user_id, "user_id")
        validate_non_empty_string(course_id, "course_id")
        if school_id is not None:
            validate_non_empty_string(school_id, "school_id")

        log.debug(
            "enroll", extra={"user_id": user_id, "course_id": course_id, "school_id": school_id}
        )
        base = (
            f"{self._transport.paths.base}/enrollments/enroll/{quote(user_id)}/{quote(course_id)}"
        )
        path = f"{base}/{quote(school_id)}" if school_id else base

        body = options.model_dump(by_alias=True, exclude_none=True) if options else {}
        response = await self._transport.post(path, body)
        return Enrollment(**response.get("data", {}))

    async def unenroll(
        self,
        user_id: str,
        course_id: str,
        school_id: str | None = None,
    ) -> None:
        """
        Unenroll a user from a course.

        Marks the enrollment as 'tobedeleted'.

        Args:
            user_id: User ID to unenroll
            course_id: Course ID to unenroll from
            school_id: Optional school ID

        Raises:
            InputValidationError: If user_id or course_id is empty
        """
        validate_non_empty_string(user_id, "user_id")
        validate_non_empty_string(course_id, "course_id")
        if school_id is not None:
            validate_non_empty_string(school_id, "school_id")

        log.debug(
            "unenroll", extra={"user_id": user_id, "course_id": course_id, "school_id": school_id}
        )
        base = (
            f"{self._transport.paths.base}/enrollments/unenroll/{quote(user_id)}/{quote(course_id)}"
        )
        path = f"{base}/{quote(school_id)}" if school_id else base
        await self._transport.delete(path)

    async def reset_goals(self, course_id: str) -> ResetGoalsResult:
        """
        Reset enrollment goals for all users in a course.

        Args:
            course_id: Course ID to reset goals for

        Returns:
            Result with count of updated enrollments

        Raises:
            InputValidationError: If course_id is empty
        """
        validate_non_empty_string(course_id, "course_id")

        log.debug("reset_goals", extra={"course_id": course_id})
        path = f"{self._transport.paths.base}/enrollments/resetGoals/{quote(course_id)}"
        response = await self._transport.post(path, {})
        return ResetGoalsResult(**response.get("data", {}))

    async def reset_progress(self, user_id: str, course_id: str) -> None:
        """
        Reset a user's progress in a course.

        Marks all assessment results for the user/course as 'tobedeleted'.

        Args:
            user_id: User ID
            course_id: Course ID

        Raises:
            InputValidationError: If user_id or course_id is empty
        """
        validate_non_empty_string(user_id, "user_id")
        validate_non_empty_string(course_id, "course_id")

        log.debug("reset_progress", extra={"user_id": user_id, "course_id": course_id})
        path = f"{self._transport.paths.base}/enrollments/resetProgress/{quote(user_id)}/{quote(course_id)}"
        await self._transport.delete(path)

    async def get_default_class(
        self,
        course_id: str,
        school_id: str | None = None,
    ) -> DefaultClass:
        """
        Get the default class for a course.

        Args:
            course_id: Course ID
            school_id: Optional school ID

        Returns:
            Default class and term information

        Raises:
            InputValidationError: If course_id is empty
        """
        validate_non_empty_string(course_id, "course_id")
        if school_id is not None:
            validate_non_empty_string(school_id, "school_id")

        log.debug("get_default_class", extra={"course_id": course_id, "school_id": school_id})
        base = f"{self._transport.paths.base}/enrollments/defaultClass/{quote(course_id)}"
        path = f"{base}/{quote(school_id)}" if school_id else base
        response = await self._transport.get(path)
        return DefaultClass(**response.get("data", {}))
