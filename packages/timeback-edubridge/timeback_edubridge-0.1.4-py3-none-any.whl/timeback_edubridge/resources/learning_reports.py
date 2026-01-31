"""
Learning Reports Resource

Student learning reports and time tracking.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

from timeback_common import validate_non_empty_string

from ..types import MapProfile, TimeSaved

if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.learning_reports")


class LearningReportsResource:
    """
    Learning Reports resource for student progress data.

    Provides access to MAP profiles and time saved metrics.

    Example:
        ```python
        # Get MAP profile for a user
        profile = await client.learning_reports.get_map_profile("user-123")

        # Get time saved for a user
        time_saved = await client.learning_reports.get_time_saved("user-123")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def get_map_profile(self, user_id: str) -> MapProfile:
        """
        Get MAP profile for a user.

        Args:
            user_id: User ID

        Returns:
            MAP profile data

        Raises:
            InputValidationError: If user_id is empty
        """
        validate_non_empty_string(user_id, "user_id")

        log.debug("get_map_profile", extra={"user_id": user_id})
        path = f"{self._transport.paths.base}/learning-reports/map-profile/{quote(user_id)}"
        response = await self._transport.get(path)
        return MapProfile(**response.get("data", {}))

    async def get_time_saved(self, user_id: str) -> TimeSaved:
        """
        Get time saved metrics for a user.

        Args:
            user_id: User ID

        Returns:
            Time saved data

        Raises:
            InputValidationError: If user_id is empty
        """
        validate_non_empty_string(user_id, "user_id")

        log.debug("get_time_saved", extra={"user_id": user_id})
        path = f"{self._transport.paths.base}/time-saved/user/{quote(user_id)}"
        response = await self._transport.get(path)
        return TimeSaved(**response.get("data", {}))
