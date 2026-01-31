"""
Applications Resource

Manage and retrieve applications available in the system.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

from timeback_common import validate_non_empty_string

from ..types import Application, ApplicationMetrics

if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.applications")


class ApplicationsResource:
    """
    Applications resource for managing learning platforms.

    Applications represent different learning platforms or educational
    software that can be integrated with Timeback.

    Example:
        ```python
        # List all applications
        apps = await client.applications.list()

        # Get metrics for an application
        metrics = await client.applications.get_metrics("app-123")
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def list(self) -> list[Application]:
        """
        List all applications.

        Returns:
            List of applications
        """
        log.debug("list")
        path = f"{self._transport.paths.base}/applications/"
        response = await self._transport.get(path)
        return [Application(**a) for a in response.get("applications", [])]

    async def get_metrics(self, application_sourced_id: str) -> ApplicationMetrics:
        """
        Get metrics for an application.

        Args:
            application_sourced_id: Application ID

        Returns:
            Application metrics

        Raises:
            InputValidationError: If application_sourced_id is empty
        """
        validate_non_empty_string(application_sourced_id, "application_sourced_id")

        log.debug("get_metrics", extra={"application_sourced_id": application_sourced_id})
        path = f"{self._transport.paths.base}/applicationMetrics/{quote(application_sourced_id)}"
        response = await self._transport.get(path)
        return ApplicationMetrics(**response.get("data", {}))
