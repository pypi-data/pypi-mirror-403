"""User models for the Canny SDK."""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from .base import CannyModel


class UserCompany(CannyModel):
    """A company associated with a user."""

    id: str
    created: datetime
    custom_fields: Optional[dict[str, Any]] = Field(default=None, alias="customFields")
    monthly_spend: Optional[float] = Field(default=None, alias="monthlySpend")
    name: str


class User(CannyModel):
    """A user in the Canny system.

    Attributes:
        id: A unique identifier for the user.
        alias: Name used in anonymized boards.
        avatar_url: Link to the user's avatar image.
        companies: Companies the user is associated with.
        created: Time at which the user was created.
        custom_fields: Custom fields associated with the user.
        email: The user's email (can be None).
        is_admin: Whether the user is a Canny admin.
        last_activity: Last time the user interacted.
        name: The user's name.
        url: The URL of the user's profile.
        user_id: The user's unique identifier in your application.
    """

    id: str
    alias: Optional[str] = None
    avatar_url: Optional[str] = Field(default=None, alias="avatarURL")
    companies: Optional[list[UserCompany]] = None
    created: datetime
    custom_fields: Optional[dict[str, Any]] = Field(default=None, alias="customFields")
    email: Optional[str] = None
    is_admin: bool = Field(alias="isAdmin")
    last_activity: Optional[datetime] = Field(default=None, alias="lastActivity")
    name: str
    url: str
    user_id: Optional[str] = Field(default=None, alias="userID")


class UserListResponse(CannyModel):
    """Response from listing users (v2 cursor-based pagination)."""

    users: list[User]
    has_next_page: bool = Field(alias="hasNextPage")
    cursor: Optional[str] = None
