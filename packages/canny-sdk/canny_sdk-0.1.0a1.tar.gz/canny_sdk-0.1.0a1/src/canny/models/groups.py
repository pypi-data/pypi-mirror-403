"""Group models for the Canny SDK."""

from typing import Optional

from pydantic import Field

from .base import CannyModel


class Group(CannyModel):
    """A group for organizing ideas.

    Attributes:
        id: A unique identifier for the group.
        name: The name of the group.
        description: A description of the group.
        url_name: A URL-friendly identifier for the group.
    """

    id: str
    name: str
    description: Optional[str] = None
    url_name: str = Field(alias="urlName")


class GroupListResponse(CannyModel):
    """Response from listing groups."""

    groups: list[Group]
