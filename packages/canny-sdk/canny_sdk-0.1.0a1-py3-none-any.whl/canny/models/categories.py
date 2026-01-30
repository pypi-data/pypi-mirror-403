"""Category models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel


class CategoryBoard(CannyModel):
    """Simplified board object included in category responses."""

    id: str
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class Category(CannyModel):
    """A category for organizing posts on a board.

    Attributes:
        id: A unique identifier for the category.
        board: The board this category is associated with.
        created: Time at which the category was created.
        name: The name of the category.
        parent_id: The id of the parent category (None if not a subcategory).
        post_count: Number of posts assigned to this category.
        url: The URL to the board filtered by this category.
    """

    id: str
    board: Optional[CategoryBoard] = None
    created: datetime
    name: str
    parent_id: Optional[str] = Field(default=None, alias="parentID")
    post_count: int = Field(alias="postCount")
    url: str


class CategoryListResponse(CannyModel):
    """Response from listing categories."""

    categories: list[Category]
