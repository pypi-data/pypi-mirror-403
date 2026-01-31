"""
EduBridge Transport Layer
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from timeback_common import BaseTransport, EdubridgePaths, TokenManager
from timeback_common.pagination_strategies import parse_body_pagination_raw

if TYPE_CHECKING:
    import httpx


@dataclass
class PaginatedResponse:
    """Normalized paginated response."""

    data: list[Any]
    has_more: bool
    total: int | None = None


class Transport(BaseTransport):
    """HTTP transport layer for EduBridge API communication."""

    paths: EdubridgePaths

    def __init__(
        self,
        *,
        base_url: str,
        token_manager: TokenManager | None = None,
        paths: EdubridgePaths,
        timeout: float = 30.0,
        http_client: httpx.AsyncClient | None = None,
        no_auth: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            token_manager=token_manager,
            http_client=http_client,
            no_auth=no_auth,
        )
        self.paths = paths

    def _extract_error_message(self, body: Any, fallback: str) -> str:
        """
        Extract error message from EduBridge error response.

        EduBridge uses a unique error format with an `errors[]` array.
        Falls back to the base extractor if not present.
        """
        if not isinstance(body, dict):
            return fallback

        # Standard error format
        if isinstance(body.get("message"), str):
            return body["message"]

        # EduBridge array format
        errors = body.get("errors")
        if isinstance(errors, list) and errors:
            first_error = errors[0]
            if not isinstance(first_error, dict):
                return fallback

            parts: list[str] = []
            msg = first_error.get("message")
            detail = first_error.get("detail")

            if isinstance(msg, str) and msg:
                parts.append(msg)
            if isinstance(detail, str) and detail and detail != msg:
                parts.append(detail)

            meta = first_error.get("meta")
            if isinstance(meta, dict):
                issues = meta.get("issues")
                if isinstance(issues, list) and issues:
                    issue_msgs = [
                        f"{i.get('path', '?')}: {i.get('message', '?')}"
                        for i in issues
                        if isinstance(i, dict) and i.get("path") and i.get("message")
                    ]
                    if issue_msgs:
                        parts.append(f"[{', '.join(issue_msgs)}]")

            if parts:
                return " - ".join(parts)

        return fallback

    async def request_paginated(
        self,
        path: str,
        *,
        params: dict[str, Any] | None = None,
    ) -> PaginatedResponse:
        """
        Make a paginated request using EduBridge body-based pagination metadata.
        """
        response = await self.request_raw("GET", path, params=params)
        body = response.json()
        if not isinstance(body, dict):
            body = {}

        parsed = parse_body_pagination_raw(body)
        return PaginatedResponse(
            data=parsed["data"],
            has_more=parsed["hasMore"],
            total=parsed["total"],
        )


__all__ = ["PaginatedResponse", "Transport"]
