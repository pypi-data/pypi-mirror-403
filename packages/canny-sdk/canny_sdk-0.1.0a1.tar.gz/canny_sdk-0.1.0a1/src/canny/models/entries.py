"""Changelog entry models for the Canny SDK."""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from .base import CannyModel


class EntryPostCategory(CannyModel):
    """Simplified category in entry's linked post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class EntryPostTag(CannyModel):
    """Simplified tag in entry's linked post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class EntryPost(CannyModel):
    """Simplified post object in entry responses."""

    id: str
    category: Optional[EntryPostCategory] = None
    comment_count: int = Field(alias="commentCount")
    eta: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    score: int
    status: str
    tags: list[EntryPostTag] = Field(default_factory=list)
    title: str
    url: str


class EntryReactions(CannyModel):
    """Reactions on an entry."""

    like: int = 0


class ChangelogEntry(CannyModel):
    """A changelog entry.

    Attributes:
        id: A unique identifier for the entry.
        created: Time at which the entry was created.
        labels: Labels associated with the entry.
        last_saved: Time at which the entry was last updated.
        markdown_details: The markdown contents of the entry.
        plaintext_details: The plaintext contents.
        posts: Posts linked to this entry.
        published_at: Time at which the entry was published.
        reactions: Reactions on the entry.
        scheduled_for: Time when the entry is scheduled.
        status: The status (draft, scheduled, published).
        title: The entry's title.
        types: Types (new, improved, fixed).
        url: The public URL to the entry.
    """

    id: str
    created: datetime
    labels: list[Any] = Field(default_factory=list)
    last_saved: datetime = Field(alias="lastSaved")
    markdown_details: str = Field(alias="markdownDetails")
    plaintext_details: str = Field(alias="plaintextDetails")
    posts: list[EntryPost] = Field(default_factory=list)
    published_at: Optional[datetime] = Field(default=None, alias="publishedAt")
    reactions: Optional[EntryReactions] = None
    scheduled_for: Optional[datetime] = Field(default=None, alias="scheduledFor")
    status: str
    title: str
    types: list[str] = Field(default_factory=list)
    url: str


class EntryListResponse(CannyModel):
    """Response from listing entries."""

    entries: list[ChangelogEntry]
    has_more: bool = Field(default=False, alias="hasMore")
