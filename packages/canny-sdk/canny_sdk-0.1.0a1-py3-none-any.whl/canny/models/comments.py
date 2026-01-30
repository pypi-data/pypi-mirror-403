"""Comment models for the Canny SDK."""

from datetime import datetime
from typing import Optional

from pydantic import Field

from .base import CannyModel


class CommentBoard(CannyModel):
    """Simplified board object in comment responses."""

    id: str
    created: datetime
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class CommentAuthor(CannyModel):
    """Simplified user object for comment author."""

    id: str
    created: datetime
    email: Optional[str] = None
    is_admin: bool = Field(alias="isAdmin")
    name: str
    url: str
    user_id: Optional[str] = Field(default=None, alias="userID")


class CommentPostCategory(CannyModel):
    """Simplified category object in comment's post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class CommentPostTag(CannyModel):
    """Simplified tag object in comment's post."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class CommentPost(CannyModel):
    """Simplified post object in comment responses."""

    id: str
    category: Optional[CommentPostCategory] = None
    comment_count: int = Field(alias="commentCount")
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    score: int
    status: str
    tags: list[CommentPostTag] = Field(default_factory=list)
    title: str
    url: str


class CommentReactions(CannyModel):
    """Reactions on a comment."""

    like: int = 0


class Comment(CannyModel):
    """A comment on a post.

    Attributes:
        id: A unique identifier for the comment.
        author: The user who created the comment.
        board: The board the comment is on.
        created: Time at which the comment was created.
        image_urls: URLs of images attached to the comment.
        internal: Whether this is an internal comment.
        like_count: Number of likes on the comment.
        mentions: Users mentioned in the comment.
        parent_id: ID of the parent comment (None if not a reply).
        post: The post this comment is on.
        private: Whether the comment is private from other users.
        reactions: Reactions on the comment.
        value: The text content of the comment.
    """

    id: str
    author: Optional[CommentAuthor] = None
    board: Optional[CommentBoard] = None
    created: datetime
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    internal: bool = False
    like_count: int = Field(default=0, alias="likeCount")
    mentions: list[CommentAuthor] = Field(default_factory=list)
    parent_id: Optional[str] = Field(default=None, alias="parentID")
    post: Optional[CommentPost] = None
    private: bool = False
    reactions: Optional[CommentReactions] = None
    value: str


class CommentListResponse(CannyModel):
    """Response from listing comments (v2 cursor-based pagination)."""

    comments: list[Comment]
    has_more: bool = Field(default=False, alias="hasMore")
    cursor: Optional[str] = None
