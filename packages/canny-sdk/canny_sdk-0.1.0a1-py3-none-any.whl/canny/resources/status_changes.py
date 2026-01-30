"""Status changes resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.status_changes import StatusChange, StatusChangeListResponse
from ..pagination import SkipPaginator
from .base import BaseAsyncResource, BaseResource


class StatusChangesResource(BaseResource):
    """Status changes API endpoints.

    Status changes track when posts have their status updated.
    """

    def list(
        self,
        *,
        board_id: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> StatusChangeListResponse:
        """List status changes.

        Args:
            board_id: Filter by board.
            limit: Number of status changes to return (1-100).
            skip: Number of status changes to skip.

        Returns:
            A response containing the list of status changes.
        """
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id

        response = self._http.post("status_changes/list", data)
        return StatusChangeListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[StatusChange]:
        """Iterate over all status changes with automatic pagination.

        Returns:
            An iterator over all status changes.
        """
        return SkipPaginator(
            fetch_fn=self.list,
            items_key="status_changes",
            **kwargs,
        )


class StatusChangesAsyncResource(BaseAsyncResource):
    """Async Status changes API endpoints."""

    async def list(
        self,
        *,
        board_id: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> StatusChangeListResponse:
        """List status changes."""
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id

        response = await self._http.post("status_changes/list", data)
        return StatusChangeListResponse.model_validate(response)
