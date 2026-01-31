"""
EduBridge Application Types

Types for application management.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class Application(BaseModel):
    """An application/learning platform."""

    sourced_id: str = Field(alias="sourcedId")
    name: str
    description: str | None = None
    domain: list[str]
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# APPLICATION METRICS TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class ApplicationMetrics(BaseModel):
    """Metrics for an application."""

    application_sourced_id: str = Field(alias="applicationSourcedId")
    total_users: int | None = Field(default=None, alias="totalUsers")
    active_users: int | None = Field(default=None, alias="activeUsers")
    total_sessions: int | None = Field(default=None, alias="totalSessions")
    avg_session_duration: float | None = Field(default=None, alias="avgSessionDuration")
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)
