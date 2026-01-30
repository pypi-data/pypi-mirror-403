"""Posts resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.posts import Post, PostListResponse
from ..pagination import SkipPaginator
from .base import BaseAsyncResource, BaseResource


class PostsResource(BaseResource):
    """Posts API endpoints.

    Posts are feature requests or ideas submitted to boards.
    """

    def retrieve(
        self,
        *,
        id: str | None = None,
        url_name: str | None = None,
        board_id: str | None = None,
    ) -> Post:
        """Retrieve a single post.

        Args:
            id: The unique identifier of the post.
            url_name: The URL name of the post (requires board_id).
            board_id: The board ID (required if using url_name).

        Returns:
            The post object.
        """
        data: dict[str, Any] = {}
        if id:
            data["id"] = id
        if url_name:
            data["urlName"] = url_name
        if board_id:
            data["boardID"] = board_id

        response = self._http.post("posts/retrieve", data)
        return Post.model_validate(response)

    def list(
        self,
        *,
        board_id: str | None = None,
        author_id: str | None = None,
        company_id: str | None = None,
        tag_id: str | None = None,
        owner_id: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        status: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> PostListResponse:
        """List posts with optional filtering.

        Args:
            board_id: Filter by board.
            author_id: Filter by author.
            company_id: Filter by company.
            tag_id: Filter by tag.
            owner_id: Filter by owner.
            search: Search string to filter posts.
            sort: Sort order (newest, oldest, relevance, score, trending).
            status: Filter by status.
            limit: Number of posts to return (1-100).
            skip: Number of posts to skip (for pagination).

        Returns:
            A response containing the list of posts.
        """
        data: dict[str, Any] = {
            "sort": sort,
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id
        if author_id:
            data["authorID"] = author_id
        if company_id:
            data["companyID"] = company_id
        if tag_id:
            data["tagID"] = tag_id
        if owner_id:
            data["ownerID"] = owner_id
        if search:
            data["search"] = search
        if status:
            data["status"] = status

        response = self._http.post("posts/list", data)
        return PostListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[Post]:
        """Iterate over all posts with automatic pagination.

        Args:
            **kwargs: Arguments to pass to list().

        Returns:
            An iterator over all posts.
        """
        return SkipPaginator(
            fetch_fn=self.list,
            items_key="posts",
            **kwargs,
        )

    # Write operations - these check read_only mode

    def create(
        self,
        *,
        author_id: str,
        board_id: str,
        title: str,
        details: str,
        by_id: str | None = None,
        category_id: str | None = None,
        custom_fields: dict[str, Any] | None = None,
        eta: str | None = None,
        eta_public: bool | None = None,
        owner_id: str | None = None,
        image_urls: list[str] | None = None,
        created_at: str | None = None,
    ) -> str:
        """Create a new post.

        Args:
            author_id: The unique identifier of the post's author.
            board_id: The unique identifier of the post's board.
            title: The post title.
            details: The post details.
            by_id: The admin creating the post on behalf of author.
            category_id: The category ID.
            custom_fields: Custom fields for the post.
            eta: Estimated completion date (MM/YYYY).
            eta_public: Whether ETA is visible to users.
            owner_id: The ID of the user responsible for completion.
            image_urls: URLs of post images.
            created_at: Original creation date if migrating.

        Returns:
            The ID of the created post.
        """
        self._check_write_allowed("create post")

        data: dict[str, Any] = {
            "authorID": author_id,
            "boardID": board_id,
            "title": title,
            "details": details,
        }
        if by_id:
            data["byID"] = by_id
        if category_id:
            data["categoryID"] = category_id
        if custom_fields:
            data["customFields"] = custom_fields
        if eta:
            data["eta"] = eta
        if eta_public is not None:
            data["etaPublic"] = eta_public
        if owner_id:
            data["ownerID"] = owner_id
        if image_urls:
            data["imageURLs"] = image_urls
        if created_at:
            data["createdAt"] = created_at

        response = self._http.post("posts/create", data)
        return response["id"]

    def update(
        self,
        *,
        post_id: str,
        title: str | None = None,
        details: str | None = None,
        custom_fields: dict[str, Any] | None = None,
        eta: str | None = None,
        eta_public: bool | None = None,
        owner_id: str | None = None,
        image_urls: list[str] | None = None,
    ) -> None:
        """Update an existing post.

        Args:
            post_id: The unique identifier of the post to update.
            title: New title (optional).
            details: New details (optional).
            custom_fields: Updated custom fields.
            eta: Updated ETA.
            eta_public: Updated ETA visibility.
            owner_id: Updated owner ID.
            image_urls: Updated image URLs.
        """
        self._check_write_allowed("update post")

        data: dict[str, Any] = {"postID": post_id}
        if title is not None:
            data["title"] = title
        if details is not None:
            data["details"] = details
        if custom_fields is not None:
            data["customFields"] = custom_fields
        if eta is not None:
            data["eta"] = eta
        if eta_public is not None:
            data["etaPublic"] = eta_public
        if owner_id is not None:
            data["ownerID"] = owner_id
        if image_urls is not None:
            data["imageURLs"] = image_urls

        self._http.post("posts/update", data)

    def delete(self, *, post_id: str) -> None:
        """Delete a post.

        Args:
            post_id: The unique identifier of the post to delete.
        """
        self._check_write_allowed("delete post")
        self._http.post("posts/delete", {"postID": post_id})

    def change_status(
        self,
        *,
        post_id: str,
        status: str,
        changer_id: str,
        comment: str | None = None,
        comment_image_urls: list[str] | None = None,
        should_notify_voters: bool = False,
    ) -> None:
        """Change a post's status.

        Args:
            post_id: The unique identifier of the post.
            status: The new status.
            changer_id: The ID of the admin changing the status.
            comment: Optional comment about the status change.
            comment_image_urls: Images for the comment.
            should_notify_voters: Whether to notify voters.
        """
        self._check_write_allowed("change post status")

        data: dict[str, Any] = {
            "postID": post_id,
            "status": status,
            "changerID": changer_id,
            "shouldNotifyVoters": should_notify_voters,
        }
        if comment:
            data["comment"] = comment
        if comment_image_urls:
            data["commentImageURLs"] = comment_image_urls

        self._http.post("posts/change_status", data)

    def change_category(
        self,
        *,
        post_id: str,
        category_id: str | None = None,
    ) -> None:
        """Change a post's category.

        Args:
            post_id: The unique identifier of the post.
            category_id: The new category ID (None to remove category).
        """
        self._check_write_allowed("change post category")

        data: dict[str, Any] = {"postID": post_id}
        if category_id:
            data["categoryID"] = category_id

        self._http.post("posts/change_category", data)

    def add_tag(self, *, post_id: str, tag_id: str) -> None:
        """Add a tag to a post.

        Args:
            post_id: The unique identifier of the post.
            tag_id: The unique identifier of the tag.
        """
        self._check_write_allowed("add tag to post")
        self._http.post("posts/add_tag", {"postID": post_id, "tagID": tag_id})

    def remove_tag(self, *, post_id: str, tag_id: str) -> None:
        """Remove a tag from a post.

        Args:
            post_id: The unique identifier of the post.
            tag_id: The unique identifier of the tag.
        """
        self._check_write_allowed("remove tag from post")
        self._http.post("posts/remove_tag", {"postID": post_id, "tagID": tag_id})


class PostsAsyncResource(BaseAsyncResource):
    """Async Posts API endpoints."""

    async def retrieve(
        self,
        *,
        id: str | None = None,
        url_name: str | None = None,
        board_id: str | None = None,
    ) -> Post:
        """Retrieve a single post."""
        data: dict[str, Any] = {}
        if id:
            data["id"] = id
        if url_name:
            data["urlName"] = url_name
        if board_id:
            data["boardID"] = board_id

        response = await self._http.post("posts/retrieve", data)
        return Post.model_validate(response)

    async def list(
        self,
        *,
        board_id: str | None = None,
        author_id: str | None = None,
        company_id: str | None = None,
        tag_id: str | None = None,
        owner_id: str | None = None,
        search: str | None = None,
        sort: str = "newest",
        status: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> PostListResponse:
        """List posts with optional filtering."""
        data: dict[str, Any] = {
            "sort": sort,
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id
        if author_id:
            data["authorID"] = author_id
        if company_id:
            data["companyID"] = company_id
        if tag_id:
            data["tagID"] = tag_id
        if owner_id:
            data["ownerID"] = owner_id
        if search:
            data["search"] = search
        if status:
            data["status"] = status

        response = await self._http.post("posts/list", data)
        return PostListResponse.model_validate(response)

    async def create(
        self,
        *,
        author_id: str,
        board_id: str,
        title: str,
        details: str,
        **kwargs: Any,
    ) -> str:
        """Create a new post."""
        self._check_write_allowed("create post")

        data: dict[str, Any] = {
            "authorID": author_id,
            "boardID": board_id,
            "title": title,
            "details": details,
        }
        # Add optional fields
        field_mapping = {
            "by_id": "byID",
            "category_id": "categoryID",
            "custom_fields": "customFields",
            "eta": "eta",
            "eta_public": "etaPublic",
            "owner_id": "ownerID",
            "image_urls": "imageURLs",
            "created_at": "createdAt",
        }
        for kwarg, api_key in field_mapping.items():
            if kwarg in kwargs and kwargs[kwarg] is not None:
                data[api_key] = kwargs[kwarg]

        response = await self._http.post("posts/create", data)
        return response["id"]

    async def delete(self, *, post_id: str) -> None:
        """Delete a post."""
        self._check_write_allowed("delete post")
        await self._http.post("posts/delete", {"postID": post_id})
