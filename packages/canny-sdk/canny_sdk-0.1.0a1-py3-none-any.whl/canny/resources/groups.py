"""Groups resource for the Canny SDK."""

from __future__ import annotations

from ..models.groups import Group, GroupListResponse
from .base import BaseAsyncResource, BaseResource


class GroupsResource(BaseResource):
    """Groups API endpoints.

    Groups are used to organize ideas within a company.
    """

    def retrieve(self, *, id: str) -> Group:
        """Retrieve a single group by ID.

        Args:
            id: The unique identifier of the group.

        Returns:
            The group object.
        """
        response = self._http.post("groups/retrieve", {"id": id})
        return Group.model_validate(response)

    def list(self) -> GroupListResponse:
        """List all groups.

        Returns:
            A response containing the list of groups.
        """
        response = self._http.post("groups/list")
        return GroupListResponse.model_validate(response)


class GroupsAsyncResource(BaseAsyncResource):
    """Async Groups API endpoints."""

    async def retrieve(self, *, id: str) -> Group:
        """Retrieve a single group by ID."""
        response = await self._http.post("groups/retrieve", {"id": id})
        return Group.model_validate(response)

    async def list(self) -> GroupListResponse:
        """List all groups."""
        response = await self._http.post("groups/list")
        return GroupListResponse.model_validate(response)
