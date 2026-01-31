"""
Tests for analytics resource response parsing.

These tests verify that API responses are correctly parsed into typed objects,
not raw dictionaries. This ensures that utility functions like
aggregate_activity_metrics work correctly when used with API responses.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from timeback_edubridge import aggregate_activity_metrics
from timeback_edubridge.resources.analytics import (
    AnalyticsResource,
    _parse_daily_activity_map,
    _parse_weekly_facts,
)
from timeback_edubridge.types.analytics import SubjectMetrics, WeeklyFactRecord

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FACTORIES
# ═══════════════════════════════════════════════════════════════════════════════


def create_raw_subject_metrics() -> dict[str, Any]:
    """Create raw API response format for SubjectMetrics."""
    return {
        "activityMetrics": {
            "xpEarned": 100,
            "totalQuestions": 50,
            "correctQuestions": 45,
            "masteredUnits": 10,
        },
        "timeSpentMetrics": {
            "activeSeconds": 3600,
            "inactiveSeconds": 300,
            "wasteSeconds": 60,
        },
        "apps": ["TestApp"],
    }


def create_raw_daily_activity_map() -> dict[str, Any]:
    """Create raw API response for DailyActivityMap."""
    return {
        "2026-01-29": {
            "Math": create_raw_subject_metrics(),
            "Reading": create_raw_subject_metrics(),
        },
        "2026-01-30": {
            "Math": create_raw_subject_metrics(),
        },
    }


def create_raw_weekly_fact_record() -> dict[str, Any]:
    """Create raw API response format for WeeklyFactRecord."""
    return {
        "id": 12345,
        "email": "student@example.com",
        "date": "2026-01-29",
        "datetime": "2026-01-29T10:00:00Z",
        "username": "student123",
        "userGrade": "5",
        "userFamilyName": "Smith",
        "userGivenName": "John",
        "userId": "user-123",
        "subject": "Math",
        "app": "TestApp",
        "courseId": "course-456",
        "courseName": "Grade 5 Math",
        "source": "activity",
        "xpEarned": 50,
        "masteredUnits": 2,
        "totalQuestions": 10,
        "correctQuestions": 9,
        "activeSeconds": "1800",  # API returns strings for these
        "inactiveSeconds": "120",
        "wasteSeconds": "30",
        "year": 2026,  # Required fields
        "month": 1,
        "day": 29,
        "dayOfWeek": 3,  # Wednesday
    }


def create_stub_transport(response: dict[str, Any]) -> MagicMock:
    """Create a mock transport that returns the given response."""
    transport = MagicMock()
    transport.get = AsyncMock(return_value=response)
    transport.paths = MagicMock()
    transport.paths.base = "/edubridge"
    return transport


# ═══════════════════════════════════════════════════════════════════════════════
# PARSING FUNCTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseDailyActivityMap:
    """Tests for _parse_daily_activity_map helper function."""

    def test_parses_raw_dict_into_typed_objects(self) -> None:
        """Raw API response should be parsed into SubjectMetrics objects."""
        raw = create_raw_daily_activity_map()
        result = _parse_daily_activity_map(raw)

        # Should have same structure
        assert "2026-01-29" in result
        assert "Math" in result["2026-01-29"]

        # Values should be SubjectMetrics, not dicts
        metrics = result["2026-01-29"]["Math"]
        assert isinstance(metrics, SubjectMetrics)

        # Should have typed attribute access (this is what broke before!)
        assert metrics.activity_metrics.mastered_units == 10
        assert metrics.activity_metrics.xp_earned == 100
        assert metrics.time_spent_metrics.active_seconds == 3600

    def test_empty_dict_returns_empty(self) -> None:
        """Empty input should return empty dict."""
        result = _parse_daily_activity_map({})
        assert result == {}

    def test_skips_invalid_entries(self) -> None:
        """Should skip entries that aren't dicts."""
        raw = {
            "2026-01-29": {
                "Math": create_raw_subject_metrics(),
                "Invalid": "not a dict",
            },
            "invalid_date": "not a dict either",
        }
        result = _parse_daily_activity_map(raw)

        assert "2026-01-29" in result
        assert "Math" in result["2026-01-29"]
        assert "Invalid" not in result["2026-01-29"]
        assert "invalid_date" not in result


class TestParseWeeklyFacts:
    """Tests for _parse_weekly_facts helper function."""

    def test_parses_raw_list_into_typed_objects(self) -> None:
        """Raw API response should be parsed into WeeklyFactRecord objects."""
        raw = [create_raw_weekly_fact_record(), create_raw_weekly_fact_record()]
        result = _parse_weekly_facts(raw)

        assert len(result) == 2
        assert all(isinstance(r, WeeklyFactRecord) for r in result)

        # Should have typed attribute access
        first = result[0]
        assert first.id == 12345
        assert first.email == "student@example.com"
        assert first.user_grade == "5"  # snake_case from camelCase

    def test_empty_list_returns_empty(self) -> None:
        """Empty input should return empty list."""
        result = _parse_weekly_facts([])
        assert result == []

    def test_skips_invalid_entries(self) -> None:
        """Should skip entries that aren't dicts."""
        raw = [create_raw_weekly_fact_record(), "invalid", None, 123]
        result = _parse_weekly_facts(raw)  # type: ignore[arg-type]

        assert len(result) == 1
        assert isinstance(result[0], WeeklyFactRecord)


# ═══════════════════════════════════════════════════════════════════════════════
# RESOURCE METHOD TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestAnalyticsResourceParsing:
    """Tests that analytics resource methods parse responses into typed objects."""

    @pytest.mark.asyncio
    async def test_get_activity_returns_typed_objects(self) -> None:
        """get_activity should return SubjectMetrics, not raw dicts."""
        transport = create_stub_transport({"facts": create_raw_daily_activity_map()})
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        result = await analytics.get_activity(
            email="test@example.com",
            start_date="2026-01-29",
            end_date="2026-01-30",
        )

        # Should be typed SubjectMetrics objects
        metrics = result["2026-01-29"]["Math"]
        assert isinstance(metrics, SubjectMetrics)
        assert metrics.activity_metrics.mastered_units == 10

    @pytest.mark.asyncio
    async def test_get_enrollment_facts_returns_typed_objects(self) -> None:
        """get_enrollment_facts should return SubjectMetrics, not raw dicts."""
        transport = create_stub_transport({"facts": create_raw_daily_activity_map()})
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        result = await analytics.get_enrollment_facts(enrollment_id="enrollment-123")

        # Should be typed SubjectMetrics objects
        metrics = result["2026-01-29"]["Math"]
        assert isinstance(metrics, SubjectMetrics)
        assert metrics.activity_metrics.mastered_units == 10

    @pytest.mark.asyncio
    async def test_get_weekly_facts_returns_typed_objects(self) -> None:
        """get_weekly_facts should return WeeklyFactRecord, not raw dicts."""
        transport = create_stub_transport(
            {"facts": [create_raw_weekly_fact_record(), create_raw_weekly_fact_record()]}
        )
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        result = await analytics.get_weekly_facts(
            email="test@example.com",
            week_date="2026-01-29",
        )

        assert len(result) == 2
        assert all(isinstance(r, WeeklyFactRecord) for r in result)
        assert result[0].user_grade == "5"


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION TEST: aggregate_activity_metrics WITH PARSED RESPONSE
# ═══════════════════════════════════════════════════════════════════════════════


class TestAggregateActivityMetricsIntegration:
    """
    Integration tests verifying aggregate_activity_metrics works with parsed API responses.

    This is the test case that would have caught the original bug - it tests that
    API responses can be passed directly to aggregate_activity_metrics.
    """

    @pytest.mark.asyncio
    async def test_aggregate_works_with_get_activity_response(self) -> None:
        """aggregate_activity_metrics should work with get_activity response."""
        transport = create_stub_transport({"facts": create_raw_daily_activity_map()})
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        # Get the response from the API
        facts = await analytics.get_activity(
            email="test@example.com",
            start_date="2026-01-29",
            end_date="2026-01-30",
        )

        # This would have FAILED before the fix with:
        # AttributeError: 'dict' object has no attribute 'activity_metrics'
        result = aggregate_activity_metrics(facts)

        # 3 subjects across 2 days, each with 10 mastered units
        assert result.mastered_units == 30
        assert result.total_xp == 300
        assert result.total_questions == 150
        assert result.correct_questions == 135
        assert result.day_count == 2
        assert result.subject_count == 3

    @pytest.mark.asyncio
    async def test_aggregate_works_with_get_enrollment_facts_response(self) -> None:
        """aggregate_activity_metrics should work with get_enrollment_facts response."""
        transport = create_stub_transport({"facts": create_raw_daily_activity_map()})
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        # Get the response from the API
        facts = await analytics.get_enrollment_facts(enrollment_id="enrollment-123")

        # This would have FAILED before the fix
        result = aggregate_activity_metrics(facts)

        assert result.mastered_units == 30
        assert result.total_xp == 300

    @pytest.mark.asyncio
    async def test_aggregate_works_with_empty_response(self) -> None:
        """aggregate_activity_metrics should work with empty API response."""
        transport = create_stub_transport({"facts": {}})
        analytics = AnalyticsResource(transport)  # type: ignore[arg-type]

        facts = await analytics.get_enrollment_facts(enrollment_id="enrollment-123")

        # This worked before (empty dict, no iteration)
        result = aggregate_activity_metrics(facts)
        assert result.mastered_units == 0
