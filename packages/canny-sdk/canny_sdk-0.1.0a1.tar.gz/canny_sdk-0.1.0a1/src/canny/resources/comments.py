"""Comments resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.comments import Comment, CommentListResponse
from ..pagination import CursorPaginator
from .base import BaseAsyncResource, BaseResource


class CommentsResource(BaseResource):
    """Comments API endpoints.

    Comments can be left on posts by users and admins.
    """

    def retrieve(self, *, id: str) -> Comment:
        """Retrieve a single comment by ID.

        Args:
            id: The unique identifier of the comment.

        Returns:
            The comment object.
        """
        response = self._http.post("comments/retrieve", {"id": id})
        return Comment.model_validate(response)

    def list(
        self,
        *,
        author_id: str | None = None,
        board_id: str | None = None,
        company_id: str | None = None,
        post_id: str | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> CommentListResponse:
        """List comments with optional filtering (v2 cursor-based pagination).

        Args:
            author_id: Filter by author.
            board_id: Filter by board.
            company_id: Filter by company.
            post_id: Filter by post.
            limit: Number of comments to return (1-100).
            cursor: Cursor for pagination.

        Returns:
            A response containing the list of comments.
        """
        data: dict[str, Any] = {"limit": limit}
        if author_id:
            data["authorID"] = author_id
        if board_id:
            data["boardID"] = board_id
        if company_id:
            data["companyID"] = company_id
        if post_id:
            data["postID"] = post_id
        if cursor:
            data["cursor"] = cursor

        response = self._http.post("comments/list", data, api_version=2)
        return CommentListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[Comment]:
        """Iterate over all comments with automatic pagination.

        Returns:
            An iterator over all comments.
        """
        return CursorPaginator(
            fetch_fn=self.list,
            items_key="comments",
            **kwargs,
        )

    # Write operations

    def create(
        self,
        *,
        author_id: str,
        post_id: str,
        value: str,
        internal: bool = False,
        parent_id: str | None = None,
        image_urls: list[str] | None = None,
        should_notify_voters: bool = False,
    ) -> str:
        """Create a new comment.

        Args:
            author_id: The ID of the comment author.
            post_id: The ID of the post.
            value: The text content of the comment.
            internal: Whether this is an internal comment.
            parent_id: The ID of the parent comment (for replies).
            image_urls: URLs of images to attach.
            should_notify_voters: Whether to notify voters.

        Returns:
            The ID of the created comment.
        """
        self._check_write_allowed("create comment")

        data: dict[str, Any] = {
            "authorID": author_id,
            "postID": post_id,
            "value": value,
            "internal": internal,
            "shouldNotifyVoters": should_notify_voters,
        }
        if parent_id:
            data["parentID"] = parent_id
        if image_urls:
            data["imageURLs"] = image_urls

        response = self._http.post("comments/create", data)
        return response["id"]

    def delete(self, *, id: str) -> None:
        """Delete a comment.

        Args:
            id: The unique identifier of the comment.
        """
        self._check_write_allowed("delete comment")
        self._http.post("comments/delete", {"id": id})


class CommentsAsyncResource(BaseAsyncResource):
    """Async Comments API endpoints."""

    async def retrieve(self, *, id: str) -> Comment:
        """Retrieve a single comment by ID."""
        response = await self._http.post("comments/retrieve", {"id": id})
        return Comment.model_validate(response)

    async def list(
        self,
        *,
        author_id: str | None = None,
        board_id: str | None = None,
        company_id: str | None = None,
        post_id: str | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> CommentListResponse:
        """List comments with optional filtering."""
        data: dict[str, Any] = {"limit": limit}
        if author_id:
            data["authorID"] = author_id
        if board_id:
            data["boardID"] = board_id
        if company_id:
            data["companyID"] = company_id
        if post_id:
            data["postID"] = post_id
        if cursor:
            data["cursor"] = cursor

        response = await self._http.post("comments/list", data, api_version=2)
        return CommentListResponse.model_validate(response)

    async def create(
        self,
        *,
        author_id: str,
        post_id: str,
        value: str,
        **kwargs: Any,
    ) -> str:
        """Create a new comment."""
        self._check_write_allowed("create comment")

        data: dict[str, Any] = {
            "authorID": author_id,
            "postID": post_id,
            "value": value,
        }
        field_mapping = {
            "internal": "internal",
            "parent_id": "parentID",
            "image_urls": "imageURLs",
            "should_notify_voters": "shouldNotifyVoters",
        }
        for kwarg, api_key in field_mapping.items():
            if kwarg in kwargs and kwargs[kwarg] is not None:
                data[api_key] = kwargs[kwarg]

        response = await self._http.post("comments/create", data)
        return response["id"]

    async def delete(self, *, id: str) -> None:
        """Delete a comment."""
        self._check_write_allowed("delete comment")
        await self._http.post("comments/delete", {"id": id})
