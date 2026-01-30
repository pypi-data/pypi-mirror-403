"""Boards resource for the Canny SDK."""

from __future__ import annotations

from ..models.boards import Board, BoardListResponse
from .base import BaseAsyncResource, BaseResource


class BoardsResource(BaseResource):
    """Boards API endpoints.

    Boards are where users can post and vote on ideas.
    """

    def retrieve(self, *, id: str) -> Board:
        """Retrieve a single board by ID.

        Args:
            id: The unique identifier of the board.

        Returns:
            The board object.
        """
        response = self._http.post("boards/retrieve", {"id": id})
        return Board.model_validate(response)

    def list(self) -> BoardListResponse:
        """List all boards.

        Returns:
            A response containing the list of boards.
        """
        response = self._http.post("boards/list")
        return BoardListResponse.model_validate(response)


class BoardsAsyncResource(BaseAsyncResource):
    """Async Boards API endpoints."""

    async def retrieve(self, *, id: str) -> Board:
        """Retrieve a single board by ID.

        Args:
            id: The unique identifier of the board.

        Returns:
            The board object.
        """
        response = await self._http.post("boards/retrieve", {"id": id})
        return Board.model_validate(response)

    async def list(self) -> BoardListResponse:
        """List all boards.

        Returns:
            A response containing the list of boards.
        """
        response = await self._http.post("boards/list")
        return BoardListResponse.model_validate(response)
