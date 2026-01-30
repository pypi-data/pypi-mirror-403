"""Votes resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.votes import Vote, VoteListResponse
from ..pagination import SkipPaginator
from .base import BaseAsyncResource, BaseResource


class VotesResource(BaseResource):
    """Votes API endpoints.

    Users can vote on posts to show interest.
    """

    def retrieve(self, *, id: str) -> Vote:
        """Retrieve a single vote by ID.

        Args:
            id: The unique identifier of the vote.

        Returns:
            The vote object.
        """
        response = self._http.post("votes/retrieve", {"id": id})
        return Vote.model_validate(response)

    def list(
        self,
        *,
        board_id: str | None = None,
        company_id: str | None = None,
        post_id: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> VoteListResponse:
        """List votes with optional filtering.

        Args:
            board_id: Filter by board.
            company_id: Filter by company.
            post_id: Filter by post.
            user_id: Filter by user.
            limit: Number of votes to return (1-100).
            skip: Number of votes to skip.

        Returns:
            A response containing the list of votes.
        """
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id
        if company_id:
            data["companyID"] = company_id
        if post_id:
            data["postID"] = post_id
        if user_id:
            data["userID"] = user_id

        response = self._http.post("votes/list", data)
        return VoteListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[Vote]:
        """Iterate over all votes with automatic pagination.

        Returns:
            An iterator over all votes.
        """
        return SkipPaginator(
            fetch_fn=self.list,
            items_key="votes",
            **kwargs,
        )

    # Write operations

    def create(
        self,
        *,
        post_id: str,
        voter_id: str,
        by_id: str | None = None,
    ) -> None:
        """Create a vote on a post.

        Args:
            post_id: The unique identifier of the post.
            voter_id: The unique identifier of the voter.
            by_id: The admin creating the vote on behalf of the user.
        """
        self._check_write_allowed("create vote")

        data: dict[str, Any] = {
            "postID": post_id,
            "voterID": voter_id,
        }
        if by_id:
            data["byID"] = by_id

        self._http.post("votes/create", data)

    def delete(self, *, post_id: str, voter_id: str) -> None:
        """Delete a vote.

        Args:
            post_id: The unique identifier of the post.
            voter_id: The unique identifier of the voter.
        """
        self._check_write_allowed("delete vote")
        self._http.post("votes/delete", {"postID": post_id, "voterID": voter_id})


class VotesAsyncResource(BaseAsyncResource):
    """Async Votes API endpoints."""

    async def retrieve(self, *, id: str) -> Vote:
        """Retrieve a single vote by ID."""
        response = await self._http.post("votes/retrieve", {"id": id})
        return Vote.model_validate(response)

    async def list(
        self,
        *,
        board_id: str | None = None,
        company_id: str | None = None,
        post_id: str | None = None,
        user_id: str | None = None,
        limit: int = 10,
        skip: int = 0,
    ) -> VoteListResponse:
        """List votes with optional filtering."""
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
        }
        if board_id:
            data["boardID"] = board_id
        if company_id:
            data["companyID"] = company_id
        if post_id:
            data["postID"] = post_id
        if user_id:
            data["userID"] = user_id

        response = await self._http.post("votes/list", data)
        return VoteListResponse.model_validate(response)

    async def create(
        self,
        *,
        post_id: str,
        voter_id: str,
        by_id: str | None = None,
    ) -> None:
        """Create a vote on a post."""
        self._check_write_allowed("create vote")

        data: dict[str, Any] = {
            "postID": post_id,
            "voterID": voter_id,
        }
        if by_id:
            data["byID"] = by_id

        await self._http.post("votes/create", data)

    async def delete(self, *, post_id: str, voter_id: str) -> None:
        """Delete a vote."""
        self._check_write_allowed("delete vote")
        await self._http.post("votes/delete", {"postID": post_id, "voterID": voter_id})
