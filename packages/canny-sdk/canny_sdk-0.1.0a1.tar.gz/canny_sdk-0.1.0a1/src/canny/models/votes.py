"""Vote models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel


class VoteBoard(CannyModel):
    """Simplified board object in vote responses."""

    id: str
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class VoteUser(CannyModel):
    """Simplified user object for vote voter/by."""

    id: str
    created: datetime
    email: Optional[str] = None
    is_admin: bool = Field(alias="isAdmin")
    name: str
    url: str
    user_id: Optional[str] = Field(default=None, alias="userID")


class VotePostCategory(CannyModel):
    """Simplified category object in vote's post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class VotePostTag(CannyModel):
    """Simplified tag object in vote's post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class VotePost(CannyModel):
    """Simplified post object in vote responses."""

    id: str
    category: Optional[VotePostCategory] = None
    comment_count: int = Field(alias="commentCount")
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    score: int
    status: str
    tags: list[VotePostTag] = Field(default_factory=list)
    title: str
    url: str


class ZendeskTicket(CannyModel):
    """Zendesk ticket information linked to a vote."""

    id: int
    url: str
    created: datetime
    subject: str
    description: str


class Vote(CannyModel):
    """A vote on a post.

    Attributes:
        id: A unique identifier for the vote.
        board: The board the vote is associated with.
        by: The admin who cast the vote on behalf of a user.
        created: Time at which the vote was first cast.
        post: The post this vote is on.
        voter: The user who cast the vote.
        vote_priority: The priority of the vote.
        zendesk_ticket: Linked Zendesk ticket (if any).
    """

    id: str
    board: Optional[VoteBoard] = None
    by: Optional[VoteUser] = None
    created: datetime
    post: Optional[VotePost] = None
    voter: Optional[VoteUser] = None
    vote_priority: Optional[str] = Field(default=None, alias="votePriority")
    zendesk_ticket: Optional[ZendeskTicket] = Field(default=None, alias="zendeskTicket")


class VoteListResponse(CannyModel):
    """Response from listing votes."""

    votes: list[Vote]
    has_more: bool = Field(default=False, alias="hasMore")
