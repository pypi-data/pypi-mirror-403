"""
Analytics Resource

Student activity data and metrics.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from timeback_common import InputValidationError, ValidationIssue, validate_non_empty_string

from ..types import (
    DailyActivityMap,
    EnrollmentFacts,
    HighestGradeMastered,
    SubjectMetrics,
    WeeklyFactRecord,
    WeeklyFacts,
)
from ..utils import normalize_date


def _parse_daily_activity_map(raw: dict[str, Any]) -> DailyActivityMap:
    """
    Parse raw API response into typed DailyActivityMap.

    The API returns raw JSON dicts, but aggregate_activity_metrics expects
    typed SubjectMetrics objects with proper attribute access.
    """
    result: DailyActivityMap = {}
    for date_key, subjects in raw.items():
        if not isinstance(subjects, dict):
            continue
        result[date_key] = {}
        for subject_key, metrics_data in subjects.items():
            if not isinstance(metrics_data, dict):
                continue
            result[date_key][subject_key] = SubjectMetrics(**metrics_data)
    return result


def _parse_weekly_facts(raw: list[dict[str, Any]]) -> WeeklyFacts:
    """
    Parse raw API response into typed WeeklyFacts (list of WeeklyFactRecord).

    The API returns raw JSON dicts, but consumers expect typed objects
    with proper attribute access.
    """
    return [WeeklyFactRecord(**record) for record in raw if isinstance(record, dict)]


def _validate_user_identifier(email: str | None, student_id: str | None, operation: str) -> None:
    """
    Validate that either email or studentId is provided.
    Raises:
        InputValidationError: If neither email nor studentId is provided
    """
    if not email and not student_id:
        raise InputValidationError(
            f"Invalid {operation} params",
            issues=[
                ValidationIssue(path="email", message="must provide either email or studentId"),
                ValidationIssue(path="studentId", message="must provide either email or studentId"),
            ],
        )


if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.analytics")


class AnalyticsResource:
    """
    Analytics resource for retrieving student activity data.

    Provides access to activity metrics, weekly facts, and grade mastery data.

    Example:
        ```python
        # Get activity for a date range
        activity = await client.analytics.get_activity(
            email="student@example.com",
            start_date="2025-01-01",
            end_date="2025-01-31",
        )

        # Get weekly facts
        facts = await client.analytics.get_weekly_facts(
            student_id="student-123",
            week_date="2025-01-15",
        )

        # Get highest grade mastered
        grade = await client.analytics.get_highest_grade_mastered(
            student_id="student-123",
            subject="Math",
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def get_activity(
        self,
        *,
        email: str | None = None,
        student_id: str | None = None,
        start_date: str,
        end_date: str,
        timezone: str | None = None,
    ) -> DailyActivityMap:
        """
        Get activity data for a date range.

        Returns metrics grouped by date, then by subject.
        Accepts dates in YYYY-MM-DD or full ISO 8601 format.

        Args:
            email: User email address
            student_id: Student sourcedId
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            timezone: IANA timezone for date calculations

        Returns:
            Activity data keyed by date, then subject

        Raises:
            InputValidationError: If neither email nor studentId is provided
        """
        # Validate email or studentId
        _validate_user_identifier(email, student_id, "activity")

        log.debug(
            "get_activity",
            extra={
                "email": email,
                "student_id": student_id,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        params: dict[str, Any] = {
            "startDate": normalize_date(start_date),
            "endDate": normalize_date(end_date),
        }
        if email:
            params["email"] = email
        if student_id:
            params["studentId"] = student_id
        if timezone:
            params["timezone"] = timezone

        response = await self._transport.get(
            f"{self._transport.paths.base}/analytics/activity",
            params=params,
        )
        raw_facts = response.get("facts", {})
        return _parse_daily_activity_map(raw_facts)

    async def get_weekly_facts(
        self,
        *,
        email: str | None = None,
        student_id: str | None = None,
        week_date: str,
        timezone: str | None = None,
    ) -> WeeklyFacts:
        """
        Get weekly facts for a student.

        Returns individual facts grouped by date for a specific week.

        Args:
            email: User email address
            student_id: Student sourcedId
            week_date: Week date (ISO format) - determines which week to query
            timezone: IANA timezone for date calculations

        Returns:
            Weekly facts data

        Raises:
            InputValidationError: If neither email nor studentId is provided
        """
        # Validate email or studentId
        _validate_user_identifier(email, student_id, "weekly facts")

        log.debug(
            "get_weekly_facts",
            extra={"email": email, "student_id": student_id, "week_date": week_date},
        )
        params: dict[str, Any] = {
            "weekDate": normalize_date(week_date),
        }
        if email:
            params["email"] = email
        if student_id:
            params["studentId"] = student_id
        if timezone:
            params["timezone"] = timezone

        response = await self._transport.get(
            f"{self._transport.paths.base}/analytics/facts/weekly",
            params=params,
        )
        raw_facts = response.get("facts", [])
        return _parse_weekly_facts(raw_facts)

    async def get_enrollment_facts(
        self,
        enrollment_id: str,
        *,
        start_date: str | None = None,
        end_date: str | None = None,
        timezone: str | None = None,
    ) -> EnrollmentFacts:
        """
        Get aggregated facts for an enrollment.

        Returns aggregated metrics for all activity within an enrollment.

        Args:
            enrollment_id: Enrollment ID
            start_date: Start date filter (ISO format)
            end_date: End date filter (ISO format)
            timezone: Timezone for date calculations

        Returns:
            Enrollment facts

        Raises:
            InputValidationError: If enrollment_id is empty
        """
        validate_non_empty_string(enrollment_id, "enrollment_id")

        log.debug(
            "get_enrollment_facts",
            extra={"enrollment_id": enrollment_id, "start_date": start_date, "end_date": end_date},
        )
        params: dict[str, Any] = {}
        if start_date:
            params["startDate"] = normalize_date(start_date)
        if end_date:
            params["endDate"] = normalize_date(end_date)
        if timezone:
            params["timezone"] = timezone

        response = await self._transport.get(
            f"{self._transport.paths.base}/analytics/enrollment/{quote(enrollment_id)}",
            params=params if params else None,
        )
        raw_facts = response.get("facts", {})
        return _parse_daily_activity_map(raw_facts)

    async def get_highest_grade_mastered(
        self,
        student_id: str,
        subject: str,
    ) -> HighestGradeMastered:
        """
        Get the highest grade a student has mastered for a subject.

        Returns grade data from multiple sources (Edulastic, placement tests, test-out).

        Args:
            student_id: Student ID
            subject: Subject name

        Returns:
            Highest grade mastered data

        Raises:
            InputValidationError: If student_id or subject is empty
        """
        validate_non_empty_string(student_id, "student_id")
        validate_non_empty_string(subject, "subject")

        log.debug(
            "get_highest_grade_mastered", extra={"student_id": student_id, "subject": subject}
        )
        path = f"{self._transport.paths.base}/analytics/highestGradeMastered/{quote(student_id)}/{quote(subject)}"
        response = await self._transport.get(path)
        return HighestGradeMastered(**response)
