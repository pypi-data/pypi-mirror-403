"""
Users Resource

Enhanced user management beyond standard OneRoster.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Literal
from urllib.parse import urlencode

from timeback_common import InputValidationError, ValidationIssue

from ..types import Role, User

if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.users")


class UsersResource:
    """
    Users resource for querying users with enhanced filtering.

    Provides role-based filtering and search capabilities beyond
    the standard OneRoster API.

    Example:
        ```python
        # List students
        students = await client.users.list_students()

        # List teachers
        teachers = await client.users.list_teachers()

        # Search users by role
        results = await client.users.search(
            roles=["student"],
            search="john",
        )
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def list(
        self,
        *,
        roles: list[Role],
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        order_by: Literal["asc", "desc"] | None = None,
        filter: str | None = None,
        search: str | None = None,
        org_sourced_ids: list[str] | None = None,
    ) -> list[User]:
        """
        List users with filtering.

        Returns users who have exclusively the specified role(s) and no other roles.

        Args:
            roles: Roles to filter by (required)
            fields: Fields to include in response
            limit: Maximum items to return
            offset: Items to skip
            sort: Field to sort by
            order_by: Sort order
            filter: OneRoster filter expression
            search: Free-text search
            org_sourced_ids: Organization IDs to filter by

        Returns:
            List of matching users

        Raises:
            InputValidationError: If roles is empty
        """
        # Validate roles is non-empty
        if not roles:
            raise InputValidationError(
                "Invalid users list params",
                issues=[ValidationIssue(path="roles", message="roles must not be empty")],
            )

        log.debug(
            "list", extra={"roles": roles, "limit": limit, "offset": offset, "search": search}
        )
        # Build query params
        params: list[tuple[str, str]] = []

        if fields:
            params.append(("fields", fields))
        if limit is not None:
            params.append(("limit", str(limit)))
        if offset is not None:
            params.append(("offset", str(offset)))
        if sort:
            params.append(("sort", sort))
        if order_by:
            params.append(("orderBy", order_by))
        if filter:
            params.append(("filter", filter))
        if search:
            params.append(("search", search))

        # Add multiple roles params
        for role in roles:
            params.append(("roles", role))

        # Add multiple org IDs if provided
        if org_sourced_ids:
            for org_id in org_sourced_ids:
                params.append(("orgSourcedIds", org_id))

        query_string = urlencode(params) if params else ""
        path = f"{self._transport.paths.base}/users/"
        if query_string:
            path = f"{path}?{query_string}"

        response = await self._transport.get(path)
        return [User(**u) for u in response.get("users", [])]

    async def list_students(
        self,
        *,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        order_by: Literal["asc", "desc"] | None = None,
        filter: str | None = None,
        search: str | None = None,
        org_sourced_ids: list[str] | None = None,
    ) -> list[User]:
        """
        List all students.

        Convenience method for listing users with student role.

        Returns:
            List of students
        """
        log.debug("list_students", extra={"limit": limit, "offset": offset, "search": search})
        return await self.list(
            roles=["student"],
            fields=fields,
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            search=search,
            org_sourced_ids=org_sourced_ids,
        )

    async def list_teachers(
        self,
        *,
        fields: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
        sort: str | None = None,
        order_by: Literal["asc", "desc"] | None = None,
        filter: str | None = None,
        search: str | None = None,
        org_sourced_ids: list[str] | None = None,
    ) -> list[User]:
        """
        List all teachers.

        Convenience method for listing users with teacher role.

        Returns:
            List of teachers
        """
        log.debug("list_teachers", extra={"limit": limit, "offset": offset, "search": search})
        return await self.list(
            roles=["teacher"],
            fields=fields,
            limit=limit,
            offset=offset,
            sort=sort,
            order_by=order_by,
            filter=filter,
            search=search,
            org_sourced_ids=org_sourced_ids,
        )

    async def search(
        self,
        roles: list[Role],
        search: str,
        limit: int = 100,
    ) -> list[User]:
        """
        Search users by role.

        Args:
            roles: Roles to filter by
            search: Search term
            limit: Maximum results

        Returns:
            List of matching users
        """
        log.debug("search", extra={"roles": roles, "search": search, "limit": limit})
        return await self.list(roles=roles, search=search, limit=limit)
