"""Roadmap models for the Canny SDK."""

from datetime import datetime

from pydantic import Field

from .base import CannyModel


class Roadmap(CannyModel):
    """A roadmap for organizing posts.

    Attributes:
        id: A unique identifier for the roadmap.
        archived: Whether the roadmap has been archived.
        created: Time at which the roadmap was created.
        name: The name of the roadmap.
        post_count: Number of posts associated with the roadmap.
        url: The URL to the roadmap.
    """

    id: str
    archived: bool = False
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class RoadmapListResponse(CannyModel):
    """Response from listing roadmaps."""

    roadmaps: list[Roadmap]
