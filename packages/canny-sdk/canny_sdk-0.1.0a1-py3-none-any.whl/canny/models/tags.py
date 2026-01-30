"""Tag models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel


class TagBoard(CannyModel):
    """Simplified board object included in tag responses."""

    id: str
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class Tag(CannyModel):
    """A tag for labeling posts on a board.

    Attributes:
        id: A unique identifier for the tag.
        board: The board this tag is associated with.
        created: Time at which the tag was created.
        name: The name of the tag.
        post_count: Number of posts assigned this tag.
        url: The URL to the board filtered by this tag.
    """

    id: str
    board: Optional[TagBoard] = None
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class TagListResponse(CannyModel):
    """Response from listing tags."""

    tags: list[Tag]
