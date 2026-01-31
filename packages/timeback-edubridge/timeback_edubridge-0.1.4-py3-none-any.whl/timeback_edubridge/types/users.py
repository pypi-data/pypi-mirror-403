"""
EduBridge User Types

Types for user management.
"""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from .base import GUIDRef, GUIDRefBase, Role, Status

# ═══════════════════════════════════════════════════════════════════════════════
# USER TYPES
# ═══════════════════════════════════════════════════════════════════════════════


class UserId(BaseModel):
    """User identifier (external ID)."""

    type: str
    identifier: str


class UserRole(BaseModel):
    """User role assignment."""

    role_type: Literal["primary", "secondary"] = Field(alias="roleType")
    role: Role
    org: GUIDRefBase
    user_profile: str | None = Field(default=None, alias="userProfile")
    metadata: dict[str, Any] | None = None
    begin_date: str | None = Field(default=None, alias="beginDate")
    end_date: str | None = Field(default=None, alias="endDate")

    model_config = ConfigDict(populate_by_name=True)


class UserCredential(BaseModel):
    """Application credentials for a user."""

    id: str
    type: str
    username: str
    password: str | None = None


class UserApp(BaseModel):
    """Application info within a user profile."""

    sourced_id: str = Field(alias="sourcedId")
    name: str
    description: str | None = None
    domain: list[str]
    metadata: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True)


class UserProfile(BaseModel):
    """User profile for an application."""

    profile_id: str = Field(alias="profileId")
    profile_type: str = Field(alias="profileType")
    vendor_id: str = Field(alias="vendorId")
    application_id: str = Field(alias="applicationId")
    description: str | None = None
    app: UserApp
    credentials: list[UserCredential]

    model_config = ConfigDict(populate_by_name=True)


class PrimaryOrg(BaseModel):
    """Primary organization reference."""

    sourced_id: str = Field(alias="sourcedId")
    name: str

    model_config = ConfigDict(populate_by_name=True)


class User(BaseModel):
    """A user in the system."""

    sourced_id: str = Field(alias="sourcedId")
    status: Status
    date_last_modified: str = Field(alias="dateLastModified")
    metadata: dict[str, Any] | None = None
    user_master_identifier: str | None = Field(default=None, alias="userMasterIdentifier")
    username: str | None = None
    user_ids: list[UserId] = Field(alias="userIds")
    enabled_user: Literal["true", "false"] = Field(alias="enabledUser")
    given_name: str = Field(alias="givenName")
    family_name: str = Field(alias="familyName")
    middle_name: str | None = Field(default=None, alias="middleName")
    roles: list[UserRole]
    agents: list[GUIDRef]
    user_profiles: list[UserProfile] = Field(alias="userProfiles")
    primary_org: PrimaryOrg | None = Field(default=None, alias="primaryOrg")

    model_config = ConfigDict(populate_by_name=True)
