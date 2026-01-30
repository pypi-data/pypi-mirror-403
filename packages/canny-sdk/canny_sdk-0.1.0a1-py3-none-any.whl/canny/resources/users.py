"""Users resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.users import User, UserListResponse
from ..pagination import CursorPaginator
from .base import BaseAsyncResource, BaseResource


class UsersResource(BaseResource):
    """Users API endpoints.

    Users can create posts, votes, and comments.
    """

    def retrieve(
        self,
        *,
        id: str | None = None,
        email: str | None = None,
        user_id: str | None = None,
    ) -> User:
        """Retrieve a single user.

        Args:
            id: The Canny ID of the user.
            email: The email of the user.
            user_id: Your application's user ID.

        Returns:
            The user object.
        """
        data: dict[str, Any] = {}
        if id:
            data["id"] = id
        if email:
            data["email"] = email
        if user_id:
            data["userID"] = user_id

        response = self._http.post("users/retrieve", data)
        return User.model_validate(response)

    def list(
        self,
        *,
        limit: int = 10,
        cursor: str | None = None,
    ) -> UserListResponse:
        """List users with cursor-based pagination (v2 API).

        Args:
            limit: Number of users to return (1-100).
            cursor: Cursor for pagination.

        Returns:
            A response containing the list of users.
        """
        data: dict[str, Any] = {"limit": limit}
        if cursor:
            data["cursor"] = cursor

        response = self._http.post("users/list", data, api_version=2)
        return UserListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[User]:
        """Iterate over all users with automatic pagination.

        Returns:
            An iterator over all users.
        """
        return CursorPaginator(
            fetch_fn=self.list,
            items_key="users",
            **kwargs,
        )

    # Write operations

    def create_or_update(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        user_id: str | None = None,
        avatar_url: str | None = None,
        companies: list[dict[str, Any]] | None = None,
        custom_fields: dict[str, Any] | None = None,
        created: str | None = None,
    ) -> str:
        """Create or update a user.

        Args:
            email: The user's email.
            name: The user's name.
            user_id: Your application's user ID.
            avatar_url: URL to the user's avatar.
            companies: Companies to associate with the user.
            custom_fields: Custom fields for the user.
            created: Creation date if migrating.

        Returns:
            The ID of the user.
        """
        self._check_write_allowed("create or update user")

        data: dict[str, Any] = {}
        if email:
            data["email"] = email
        if name:
            data["name"] = name
        if user_id:
            data["userID"] = user_id
        if avatar_url:
            data["avatarURL"] = avatar_url
        if companies:
            data["companies"] = companies
        if custom_fields:
            data["customFields"] = custom_fields
        if created:
            data["created"] = created

        response = self._http.post("users/create_or_update", data)
        return response["id"]

    def delete(self, *, user_id: str) -> None:
        """Delete a user.

        Args:
            user_id: The Canny ID of the user to delete.
        """
        self._check_write_allowed("delete user")
        self._http.post("users/delete", {"userID": user_id})

    def remove_from_company(self, *, user_id: str, company_id: str) -> None:
        """Remove a user from a company.

        Args:
            user_id: The Canny ID of the user.
            company_id: The ID of the company.
        """
        self._check_write_allowed("remove user from company")
        self._http.post(
            "users/remove_from_company",
            {"userID": user_id, "companyID": company_id},
        )


class UsersAsyncResource(BaseAsyncResource):
    """Async Users API endpoints."""

    async def retrieve(
        self,
        *,
        id: str | None = None,
        email: str | None = None,
        user_id: str | None = None,
    ) -> User:
        """Retrieve a single user."""
        data: dict[str, Any] = {}
        if id:
            data["id"] = id
        if email:
            data["email"] = email
        if user_id:
            data["userID"] = user_id

        response = await self._http.post("users/retrieve", data)
        return User.model_validate(response)

    async def list(
        self,
        *,
        limit: int = 10,
        cursor: str | None = None,
    ) -> UserListResponse:
        """List users with cursor-based pagination (v2 API)."""
        data: dict[str, Any] = {"limit": limit}
        if cursor:
            data["cursor"] = cursor

        response = await self._http.post("users/list", data, api_version=2)
        return UserListResponse.model_validate(response)

    async def create_or_update(
        self,
        *,
        email: str | None = None,
        name: str | None = None,
        user_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Create or update a user."""
        self._check_write_allowed("create or update user")

        data: dict[str, Any] = {}
        if email:
            data["email"] = email
        if name:
            data["name"] = name
        if user_id:
            data["userID"] = user_id

        field_mapping = {
            "avatar_url": "avatarURL",
            "companies": "companies",
            "custom_fields": "customFields",
            "created": "created",
        }
        for kwarg, api_key in field_mapping.items():
            if kwarg in kwargs and kwargs[kwarg] is not None:
                data[api_key] = kwargs[kwarg]

        response = await self._http.post("users/create_or_update", data)
        return response["id"]

    async def delete(self, *, user_id: str) -> None:
        """Delete a user."""
        self._check_write_allowed("delete user")
        await self._http.post("users/delete", {"userID": user_id})
