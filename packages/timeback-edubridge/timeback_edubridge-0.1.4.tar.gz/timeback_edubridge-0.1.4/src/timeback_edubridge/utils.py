"""
EduBridge Utility Functions

Internal utilities for the EduBridge client.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from timeback_common import normalize_boolean, normalize_date

from .types.analytics import AggregatedMetrics, DailyActivityMap

if TYPE_CHECKING:
    from .types.users import User

# Re-export for backwards compatibility
__all__ = [
    "AggregatedMetrics",
    "aggregate_activity_metrics",
    "normalize_boolean",
    "normalize_date",
    "normalize_user",
]

# ═══════════════════════════════════════════════════════════════════════════════
# TYPE NORMALIZATION
# ═══════════════════════════════════════════════════════════════════════════════


T = TypeVar("T", bound="User")


def normalize_user[T: "User"](user: T) -> T:
    """
    Normalize a User object from the API.

    Applies all necessary field normalizations to ensure consistent types.
    Currently normalizes:
    - `enabled_user`: string → boolean

    Args:
        user: Raw user from the API

    Returns:
        User with normalized fields

    Note:
        This function modifies the user object in-place and returns it.
        The Pydantic model's `enabled_user` field may be typed as `Literal["true", "false"]`
        from the API, but after normalization it will be a boolean.
    """
    # Access the underlying attribute to normalize it
    # Since Pydantic models are mutable by default, we can modify in place
    object.__setattr__(user, "enabled_user", normalize_boolean(user.enabled_user))
    return user


# ═══════════════════════════════════════════════════════════════════════════════
# METRICS AGGREGATION
# ═══════════════════════════════════════════════════════════════════════════════


def aggregate_activity_metrics(data: DailyActivityMap) -> AggregatedMetrics:
    """
    Aggregate activity metrics from a DailyActivityMap.

    Sums up all metrics across dates and subjects into a single totals object.

    Args:
        data: Activity data grouped by date and subject

    Returns:
        Aggregated totals

    Example:
        ```python
        activity = await client.analytics.get_activity(...)
        totals = aggregate_activity_metrics(activity)
        print(f"Total XP: {totals.total_xp}")
        ```
    """
    total_xp: float = 0
    total_questions: int = 0
    correct_questions: int = 0
    mastered_units: int = 0
    active_seconds: float = 0
    inactive_seconds: float = 0
    waste_seconds: float = 0
    subject_count: int = 0

    dates = list(data.keys())
    day_count = len(dates)

    for date in dates:
        subjects = data.get(date)
        if subjects is None:
            continue

        for subject_key in subjects:
            metrics = subjects.get(subject_key)
            if metrics is None:
                continue

            subject_count += 1
            total_xp += metrics.activity_metrics.xp_earned
            total_questions += metrics.activity_metrics.total_questions
            correct_questions += metrics.activity_metrics.correct_questions
            mastered_units += metrics.activity_metrics.mastered_units
            active_seconds += metrics.time_spent_metrics.active_seconds
            inactive_seconds += metrics.time_spent_metrics.inactive_seconds
            waste_seconds += metrics.time_spent_metrics.waste_seconds

    return AggregatedMetrics(
        totalXp=total_xp,
        totalQuestions=total_questions,
        correctQuestions=correct_questions,
        masteredUnits=mastered_units,
        activeSeconds=active_seconds,
        inactiveSeconds=inactive_seconds,
        wasteSeconds=waste_seconds,
        dayCount=day_count,
        subjectCount=subject_count,
    )
