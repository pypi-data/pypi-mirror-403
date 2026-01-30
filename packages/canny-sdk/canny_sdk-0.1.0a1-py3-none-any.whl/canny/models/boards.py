"""Board models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel


class Board(CannyModel):
    """A board where users can post and vote on ideas.

    Attributes:
        id: A unique identifier for the board.
        created: Time at which the board was created.
        is_private: Whether the board is set as private.
        name: The board's name.
        post_count: Number of non-deleted posts on the board.
        private_comments: Whether comments are private from other users.
        url: The URL to the board's page.
    """

    id: str
    created: datetime
    is_private: Optional[bool] = Field(default=None, alias="isPrivate")
    name: str
    post_count: int = Field(alias="postCount")
    private_comments: Optional[bool] = Field(default=None, alias="privateComments")
    url: str


class BoardListResponse(CannyModel):
    """Response from listing boards."""

    boards: list[Board]
