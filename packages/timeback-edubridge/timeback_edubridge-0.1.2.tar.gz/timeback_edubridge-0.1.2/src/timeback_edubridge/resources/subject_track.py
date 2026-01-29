"""
Subject Track Resource

Manage subject track mappings.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import quote

from timeback_common import validate_non_empty_string, validate_with_schema

from ..types import SubjectTrack, SubjectTrackGroup, SubjectTrackUpsertInput

if TYPE_CHECKING:
    from ..lib.transport import Transport

log = logging.getLogger("timeback_edubridge.subject_track")


class SubjectTrackResource:
    """
    Subject Track resource for managing subject-to-course mappings.

    Subject tracks determine the target course for each subject and grade level.
    For example, for subject 'Math' grade level '9', the target course can be
    'Math Academy 9th Grade'.

    Example:
        ```python
        # List all subject tracks
        tracks = await client.subject_tracks.list()

        # Create or update a subject track
        track = await client.subject_tracks.upsert(
            id="track-123",
            data=SubjectTrackInput(
                subject="Math",
                grade_level="9",
                target_course_id="course-456",
            ),
        )

        # Delete a subject track
        await client.subject_tracks.delete("track-123")

        # List subject track groups
        groups = await client.subject_tracks.list_groups()
        ```
    """

    def __init__(self, transport: Transport) -> None:
        self._transport = transport

    async def list(self) -> list[SubjectTrack]:
        """
        List all subject tracks.

        Returns:
            List of subject tracks
        """
        log.debug("list")
        path = f"{self._transport.paths.base}/subject-track/"
        response = await self._transport.get(path)
        return [SubjectTrack(**t) for t in response.get("subjectTrack", [])]

    async def upsert(
        self,
        data: SubjectTrackUpsertInput,
    ) -> SubjectTrack:
        """
        Create or update a subject track.

        This is an upsert operation - if the subject track with the given id
        exists it will be updated, otherwise it will be created.

        Args:
            data: Subject track data including id

        Returns:
            The created or updated subject track

        Raises:
            InputValidationError: If id or any required field is empty

        Example:
            ```python
            track = await client.subject_tracks.upsert(
                SubjectTrackUpsertInput(
                    id="track-123",
                    subject="Math",
                    grade_level="9",
                    target_course_id="course-456",
                )
            )
            ```
        """
        # Validate full input including id via schema
        validate_with_schema(SubjectTrackUpsertInput, data, "subject track")

        log.debug("upsert", extra={"id": data.id})
        path = f"{self._transport.paths.base}/subject-track/"
        body = data.model_dump(by_alias=True)
        response = await self._transport.put(path, body)
        return SubjectTrack(**response.get("subjectTrack", {}))

    async def delete(self, id: str) -> None:
        """
        Delete a subject track.

        Args:
            id: Subject track ID

        Raises:
            InputValidationError: If id is empty
        """
        validate_non_empty_string(id, "id")

        log.debug("delete", extra={"id": id})
        path = f"{self._transport.paths.base}/subject-track/{quote(id)}"
        await self._transport.delete(path)

    async def list_groups(self) -> list[SubjectTrackGroup]:
        """
        List all subject track groups.

        Returns:
            List of subject track groups
        """
        log.debug("list_groups")
        path = f"{self._transport.paths.base}/subject-track/groups"
        response = await self._transport.get(path)
        return [SubjectTrackGroup(**g) for g in response.get("groups", [])]
