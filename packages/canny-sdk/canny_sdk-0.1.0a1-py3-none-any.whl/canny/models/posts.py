"""Post models for the Canny SDK."""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from .base import CannyModel
from .boards import Board
from .roadmaps import Roadmap
from .users import User


class JiraIssue(CannyModel):
    """A linked Jira issue."""

    id: str
    key: str
    url: str


class JiraIntegration(CannyModel):
    """Jira integration data for a post."""

    linked_issues: list[JiraIssue] = Field(default_factory=list, alias="linkedIssues")


class LinearIntegration(CannyModel):
    """Linear integration data for a post."""

    linked_issue_ids: list[str] = Field(default_factory=list, alias="linkedIssueIDs")


class ClickUpTask(CannyModel):
    """A linked ClickUp task."""

    id: str
    link_id: str = Field(alias="linkID")
    name: str
    post_id: str = Field(alias="postID")
    status: str
    url: str


class ClickUpIntegration(CannyModel):
    """ClickUp integration data for a post."""

    linked_tasks: list[ClickUpTask] = Field(default_factory=list, alias="linkedTasks")


class MergedPost(CannyModel):
    """A post that was merged into another post."""

    id: str
    created: datetime
    details: str
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    title: str


class MergeHistoryEntry(CannyModel):
    """An entry in the merge history."""

    created: datetime
    post: MergedPost


class ChangeComment(CannyModel):
    """A comment attached to a status change."""

    value: str
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")


class PostCategory(CannyModel):
    """Simplified category object in post responses."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str
    parent_id: Optional[str] = Field(default=None, alias="parentID")


class PostTag(CannyModel):
    """Simplified tag object in post responses."""

    id: str
    name: str
    post_count: int = Field(alias="postCount")
    url: str


class Post(CannyModel):
    """A post (feature request/idea) on a board.

    Attributes:
        id: A unique identifier for the post.
        author: The user who authored the post.
        board: The board this post is on.
        by: The admin who created the post on behalf of the author.
        category: The category this post is assigned to.
        change_comment: Comment attached to the most recent status change.
        clickup: ClickUp integration data.
        comment_count: Number of non-deleted comments.
        created: Time at which the post was created.
        custom_fields: Custom fields associated with the post.
        details: The post's detailed description.
        eta: Estimated delivery date (MM/YYYY format).
        image_urls: URLs of images attached to the post.
        jira: Jira integration data.
        linear: Linear integration data.
        merge_history: History of posts merged into this one.
        owner: The owner of the post.
        roadmaps: Roadmaps this post is on.
        score: Number of votes on this post.
        status: The post's status.
        status_changed_at: Time of last status change.
        tags: Tags assigned to this post.
        title: The post's title.
        url: The URL to the post's page.
    """

    id: str
    author: Optional[User] = None
    board: Optional[Board] = None
    by: Optional[User] = None
    category: Optional[PostCategory] = None
    change_comment: Optional[ChangeComment] = Field(default=None, alias="changeComment")
    clickup: Optional[ClickUpIntegration] = None
    comment_count: int = Field(default=0, alias="commentCount")
    created: datetime
    custom_fields: Optional[list[dict[str, Any]]] = Field(default=None, alias="customFields")
    details: Optional[str] = None
    eta: Optional[str] = None
    image_urls: list[str] = Field(default_factory=list, alias="imageURLs")
    jira: Optional[JiraIntegration] = None
    linear: Optional[LinearIntegration] = None
    merge_history: Optional[list[MergeHistoryEntry]] = Field(default=None, alias="mergeHistory")
    owner: Optional[User] = None
    roadmaps: Optional[list[Roadmap]] = None
    score: int = 0
    status: str = "open"
    status_changed_at: Optional[datetime] = Field(default=None, alias="statusChangedAt")
    tags: list[PostTag] = Field(default_factory=list)
    title: str
    url: str


class PostListResponse(CannyModel):
    """Response from listing posts."""

    posts: list[Post]
    has_more: bool = Field(default=False, alias="hasMore")
