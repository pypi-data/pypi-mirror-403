"""Categories resource for the Canny SDK."""

from __future__ import annotations

from typing import Any

from ..models.categories import Category, CategoryListResponse
from .base import BaseAsyncResource, BaseResource


class CategoriesResource(BaseResource):
    """Categories API endpoints.

    Categories are used to organize posts on a board.
    """

    def retrieve(self, *, id: str) -> Category:
        """Retrieve a single category by ID.

        Args:
            id: The unique identifier of the category.

        Returns:
            The category object.
        """
        response = self._http.post("categories/retrieve", {"id": id})
        return Category.model_validate(response)

    def list(self, *, board_id: str) -> CategoryListResponse:
        """List all categories for a board.

        Args:
            board_id: The unique identifier of the board.

        Returns:
            A response containing the list of categories.
        """
        response = self._http.post("categories/list", {"boardID": board_id})
        return CategoryListResponse.model_validate(response)

    # Write operations

    def create(
        self,
        *,
        board_id: str,
        name: str,
        parent_id: str | None = None,
    ) -> str:
        """Create a new category.

        Args:
            board_id: The unique identifier of the board.
            name: The name of the category.
            parent_id: The ID of the parent category (for subcategories).

        Returns:
            The ID of the created category.
        """
        self._check_write_allowed("create category")

        data: dict[str, Any] = {
            "boardID": board_id,
            "name": name,
        }
        if parent_id:
            data["parentID"] = parent_id

        response = self._http.post("categories/create", data)
        return response["id"]

    def delete(self, *, id: str) -> None:
        """Delete a category.

        Args:
            id: The unique identifier of the category.
        """
        self._check_write_allowed("delete category")
        self._http.post("categories/delete", {"id": id})


class CategoriesAsyncResource(BaseAsyncResource):
    """Async Categories API endpoints."""

    async def retrieve(self, *, id: str) -> Category:
        """Retrieve a single category by ID."""
        response = await self._http.post("categories/retrieve", {"id": id})
        return Category.model_validate(response)

    async def list(self, *, board_id: str) -> CategoryListResponse:
        """List all categories for a board."""
        response = await self._http.post("categories/list", {"boardID": board_id})
        return CategoryListResponse.model_validate(response)

    async def create(
        self,
        *,
        board_id: str,
        name: str,
        parent_id: str | None = None,
    ) -> str:
        """Create a new category."""
        self._check_write_allowed("create category")

        data: dict[str, Any] = {
            "boardID": board_id,
            "name": name,
        }
        if parent_id:
            data["parentID"] = parent_id

        response = await self._http.post("categories/create", data)
        return response["id"]

    async def delete(self, *, id: str) -> None:
        """Delete a category."""
        self._check_write_allowed("delete category")
        await self._http.post("categories/delete", {"id": id})
