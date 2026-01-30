"""Status change models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel
from .posts import Post
from .users import User


class StatusChangeComment(CannyModel):
    """A comment attached to a status change."""

    value: str
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")


class StatusChange(CannyModel):
    """A status change on a post.

    Attributes:
        id: A unique identifier for the status change.
        change_comment: Comment attached to this status change.
        changer: The user who changed the status.
        created: Time at which the status was changed.
        post: The post that had its status changed.
        status: The status the post was changed to.
    """

    id: str
    change_comment: Optional[StatusChangeComment] = Field(default=None, alias="changeComment")
    changer: Optional[User] = None
    created: datetime
    post: Optional[Post] = None
    status: str


class StatusChangeListResponse(CannyModel):
    """Response from listing status changes."""

    status_changes: list[StatusChange] = Field(alias="statusChanges")
    has_more: bool = Field(default=False, alias="hasMore")
