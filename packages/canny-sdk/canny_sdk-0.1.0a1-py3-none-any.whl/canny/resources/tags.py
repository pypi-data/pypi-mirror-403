"""Tags resource for the Canny SDK."""

from __future__ import annotations

from typing import Any

from ..models.tags import Tag, TagListResponse
from .base import BaseAsyncResource, BaseResource


class TagsResource(BaseResource):
    """Tags API endpoints.

    Tags are used to label and filter posts on a board.
    """

    def retrieve(self, *, id: str) -> Tag:
        """Retrieve a single tag by ID.

        Args:
            id: The unique identifier of the tag.

        Returns:
            The tag object.
        """
        response = self._http.post("tags/retrieve", {"id": id})
        return Tag.model_validate(response)

    def list(self, *, board_id: str) -> TagListResponse:
        """List all tags for a board.

        Args:
            board_id: The unique identifier of the board.

        Returns:
            A response containing the list of tags.
        """
        response = self._http.post("tags/list", {"boardID": board_id})
        return TagListResponse.model_validate(response)

    # Write operations

    def create(self, *, board_id: str, name: str) -> str:
        """Create a new tag.

        Args:
            board_id: The unique identifier of the board.
            name: The name of the tag.

        Returns:
            The ID of the created tag.
        """
        self._check_write_allowed("create tag")

        data: dict[str, Any] = {
            "boardID": board_id,
            "name": name,
        }

        response = self._http.post("tags/create", data)
        return response["id"]


class TagsAsyncResource(BaseAsyncResource):
    """Async Tags API endpoints."""

    async def retrieve(self, *, id: str) -> Tag:
        """Retrieve a single tag by ID."""
        response = await self._http.post("tags/retrieve", {"id": id})
        return Tag.model_validate(response)

    async def list(self, *, board_id: str) -> TagListResponse:
        """List all tags for a board."""
        response = await self._http.post("tags/list", {"boardID": board_id})
        return TagListResponse.model_validate(response)

    async def create(self, *, board_id: str, name: str) -> str:
        """Create a new tag."""
        self._check_write_allowed("create tag")

        data: dict[str, Any] = {
            "boardID": board_id,
            "name": name,
        }

        response = await self._http.post("tags/create", data)
        return response["id"]
