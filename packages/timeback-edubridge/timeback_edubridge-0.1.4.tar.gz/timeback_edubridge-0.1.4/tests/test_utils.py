"""
EduBridge Utility Function Tests

Tests for utility functions: normalizeBoolean, normalizeUser, normalizeDate, aggregateActivityMetrics.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from timeback_edubridge import (
    AggregatedMetrics,
    aggregate_activity_metrics,
    normalize_boolean,
    normalize_date,
    normalize_user,
)
from timeback_edubridge.types.analytics import (
    ActivityMetricsData,
    SubjectMetrics,
    TimeSpentMetricsData,
)


class TestNormalizeBoolean:
    """Tests for normalize_boolean utility."""

    def test_boolean_true_passthrough(self) -> None:
        """Boolean True should pass through unchanged."""
        assert normalize_boolean(True) is True

    def test_boolean_false_passthrough(self) -> None:
        """Boolean False should pass through unchanged."""
        assert normalize_boolean(False) is False

    def test_string_true_to_boolean(self) -> None:
        """String 'true' should be converted to boolean True."""
        assert normalize_boolean("true") is True

    def test_string_false_to_boolean(self) -> None:
        """String 'false' should be converted to boolean False."""
        assert normalize_boolean("false") is False

    def test_other_strings_are_false(self) -> None:
        """Other strings should be converted to False."""
        assert normalize_boolean("yes") is False
        assert normalize_boolean("1") is False
        assert normalize_boolean("") is False


class TestNormalizeDate:
    """Tests for normalize_date utility."""

    def test_none_passthrough(self) -> None:
        """None should pass through unchanged."""
        assert normalize_date(None) is None

    def test_date_only_format(self) -> None:
        """Date-only format should be expanded to full ISO."""
        result = normalize_date("2025-12-25")
        assert result == "2025-12-25T00:00:00.000Z"

    def test_full_iso_passthrough(self) -> None:
        """Full ISO format should pass through unchanged."""
        assert normalize_date("2025-12-25T10:30:00.000Z") == "2025-12-25T10:30:00.000Z"

    def test_datetime_object(self) -> None:
        """Datetime object should be converted to ISO string."""
        dt = datetime(2025, 12, 25, 10, 30, 0, 0, tzinfo=UTC)
        result = normalize_date(dt)
        assert result is not None
        assert "2025-12-25T10:30:00" in result
        assert result.endswith("Z")

    def test_datetime_with_microseconds(self) -> None:
        """Datetime with microseconds should preserve milliseconds."""
        dt = datetime(2025, 12, 25, 10, 30, 0, 123456, tzinfo=UTC)
        result = normalize_date(dt)
        assert result is not None
        assert "123Z" in result  # 123456 microseconds = 123 milliseconds

    def test_invalid_format_passthrough(self) -> None:
        """Invalid formats should pass through for API validation."""
        assert normalize_date("not-a-date") == "not-a-date"

    def test_plus_zero_offset_converted_to_z(self) -> None:
        """ISO strings with +00:00 offset should be converted to Z suffix.

        This is critical for API compatibility - Bug #3 from 2026-01-19.
        Python's datetime.isoformat() produces +00:00, but APIs expect Z.
        """
        # This is exactly what datetime.now(UTC).isoformat() produces
        result = normalize_date("2025-12-25T10:30:00+00:00")
        assert result == "2025-12-25T10:30:00Z"

    def test_plus_zero_offset_with_microseconds(self) -> None:
        """ISO strings with +00:00 and microseconds should convert to Z."""
        result = normalize_date("2025-12-25T10:30:00.123456+00:00")
        assert result == "2025-12-25T10:30:00.123456Z"


class TestNormalizeUser:
    """Tests for normalize_user utility."""

    def test_normalizes_enabled_user_string_true(self) -> None:
        """Should normalize enabledUser string 'true' to boolean True."""
        # Create a mock user-like object

        # We can't easily test this without a full User object, but we can
        # test that the function doesn't crash and modifies the attribute
        # This is a simplified test - the actual function modifies the object in place

        class MockUser(BaseModel):
            enabled_user: str = Field(alias="enabledUser")
            model_config = ConfigDict(populate_by_name=True)

        user = MockUser(enabledUser="true")
        result = normalize_user(user)  # type: ignore[type-var]

        # The function modifies in place
        assert result is user
        # Note: After normalization, enabled_user becomes a bool
        assert result.enabled_user is True  # type: ignore[comparison-overlap]


class TestAggregateActivityMetrics:
    """Tests for aggregate_activity_metrics utility."""

    def _create_subject_metrics(
        self,
        xp: float = 0,
        total_q: int = 0,
        correct_q: int = 0,
        mastered: int = 0,
        active: int = 0,
        inactive: int = 0,
        waste: int = 0,
    ) -> SubjectMetrics:
        """Helper to create SubjectMetrics."""
        return SubjectMetrics(
            activityMetrics=ActivityMetricsData(
                xpEarned=xp,
                totalQuestions=total_q,
                correctQuestions=correct_q,
                masteredUnits=mastered,
            ),
            timeSpentMetrics=TimeSpentMetricsData(
                activeSeconds=active,
                inactiveSeconds=inactive,
                wasteSeconds=waste,
            ),
            apps=["TestApp"],
        )

    def test_empty_data(self) -> None:
        """Empty data should return zero metrics."""
        result = aggregate_activity_metrics({})

        assert result.total_xp == 0
        assert result.total_questions == 0
        assert result.correct_questions == 0
        assert result.mastered_units == 0
        assert result.active_seconds == 0
        assert result.inactive_seconds == 0
        assert result.waste_seconds == 0
        assert result.day_count == 0
        assert result.subject_count == 0

    def test_single_day_single_subject(self) -> None:
        """Single day with single subject should sum correctly."""
        data = {
            "2025-01-01": {
                "Math": self._create_subject_metrics(
                    xp=100,
                    total_q=10,
                    correct_q=8,
                    mastered=2,
                    active=3600,
                    inactive=600,
                    waste=120,
                ),
            },
        }

        result = aggregate_activity_metrics(data)

        assert result.total_xp == 100
        assert result.total_questions == 10
        assert result.correct_questions == 8
        assert result.mastered_units == 2
        assert result.active_seconds == 3600
        assert result.inactive_seconds == 600
        assert result.waste_seconds == 120
        assert result.day_count == 1
        assert result.subject_count == 1

    def test_multiple_days_multiple_subjects(self) -> None:
        """Multiple days with multiple subjects should sum across all."""
        data = {
            "2025-01-01": {
                "Math": self._create_subject_metrics(xp=100, total_q=10, correct_q=8, active=1800),
                "Reading": self._create_subject_metrics(xp=50, total_q=5, correct_q=4, active=900),
            },
            "2025-01-02": {
                "Math": self._create_subject_metrics(xp=150, total_q=15, correct_q=12, active=2700),
            },
        }

        result = aggregate_activity_metrics(data)

        assert result.total_xp == 300  # 100 + 50 + 150
        assert result.total_questions == 30  # 10 + 5 + 15
        assert result.correct_questions == 24  # 8 + 4 + 12
        assert result.active_seconds == 5400  # 1800 + 900 + 2700
        assert result.day_count == 2
        assert result.subject_count == 3


class TestAggregatedMetricsType:
    """Tests for AggregatedMetrics Pydantic model."""

    def test_model_creation(self) -> None:
        """AggregatedMetrics should be creatable with all fields."""
        metrics = AggregatedMetrics(
            totalXp=100.5,
            totalQuestions=50,
            correctQuestions=45,
            masteredUnits=3,
            activeSeconds=7200,
            inactiveSeconds=600,
            wasteSeconds=120,
            dayCount=5,
            subjectCount=10,
        )

        assert metrics.total_xp == 100.5
        assert metrics.total_questions == 50
        assert metrics.day_count == 5
