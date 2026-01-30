"""Changelog entries resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.entries import ChangelogEntry, EntryListResponse
from ..pagination import SkipPaginator
from .base import BaseAsyncResource, BaseResource


class EntriesResource(BaseResource):
    """Changelog entries API endpoints.

    Entries are items in your changelog.
    """

    def list(
        self,
        *,
        label_ids: list[str] | None = None,
        limit: int = 10,
        skip: int = 0,
        sort: str = "created",
        type: str | None = None,
    ) -> EntryListResponse:
        """List changelog entries.

        Args:
            label_ids: Filter by label IDs.
            limit: Number of entries to return (1-100).
            skip: Number of entries to skip.
            sort: Sort order (created, lastSaved, nonPublishedFirst, publishedAt).
            type: Filter by type (new, improved, fixed).

        Returns:
            A response containing the list of entries.
        """
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
            "sort": sort,
        }
        if label_ids:
            data["labelIDs"] = label_ids
        if type:
            data["type"] = type

        response = self._http.post("entries/list", data)
        return EntryListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[ChangelogEntry]:
        """Iterate over all entries with automatic pagination.

        Returns:
            An iterator over all entries.
        """
        return SkipPaginator(
            fetch_fn=self.list,
            items_key="entries",
            **kwargs,
        )

    # Write operations

    def create(
        self,
        *,
        title: str,
        details: str,
        notify_users: bool = False,
        post_ids: list[str] | None = None,
        published_on: str | None = None,
        scheduled_for: str | None = None,
        label_ids: list[str] | None = None,
        types: list[str] | None = None,
    ) -> str:
        """Create a new changelog entry.

        Args:
            title: The title of the entry.
            details: The markdown content of the entry.
            notify_users: Whether to notify subscribed users.
            post_ids: IDs of posts to link to the entry.
            published_on: Publication date (ISO format) for immediate publish.
            scheduled_for: Date to schedule publication (ISO format).
            label_ids: Label IDs to assign.
            types: Types for the entry (new, improved, fixed).

        Returns:
            The ID of the created entry.
        """
        self._check_write_allowed("create changelog entry")

        data: dict[str, Any] = {
            "title": title,
            "details": details,
            "notifyUsers": notify_users,
        }
        if post_ids:
            data["postIDs"] = post_ids
        if published_on:
            data["publishedOn"] = published_on
        if scheduled_for:
            data["scheduledFor"] = scheduled_for
        if label_ids:
            data["labelIDs"] = label_ids
        if types:
            data["types"] = types

        response = self._http.post("entries/create", data)
        return response["id"]


class EntriesAsyncResource(BaseAsyncResource):
    """Async Changelog entries API endpoints."""

    async def list(
        self,
        *,
        label_ids: list[str] | None = None,
        limit: int = 10,
        skip: int = 0,
        sort: str = "created",
        type: str | None = None,
    ) -> EntryListResponse:
        """List changelog entries."""
        data: dict[str, Any] = {
            "limit": limit,
            "skip": skip,
            "sort": sort,
        }
        if label_ids:
            data["labelIDs"] = label_ids
        if type:
            data["type"] = type

        response = await self._http.post("entries/list", data)
        return EntryListResponse.model_validate(response)

    async def create(
        self,
        *,
        title: str,
        details: str,
        **kwargs: Any,
    ) -> str:
        """Create a new changelog entry."""
        self._check_write_allowed("create changelog entry")

        data: dict[str, Any] = {
            "title": title,
            "details": details,
        }
        field_mapping = {
            "notify_users": "notifyUsers",
            "post_ids": "postIDs",
            "published_on": "publishedOn",
            "scheduled_for": "scheduledFor",
            "label_ids": "labelIDs",
            "types": "types",
        }
        for kwarg, api_key in field_mapping.items():
            if kwarg in kwargs and kwargs[kwarg] is not None:
                data[api_key] = kwargs[kwarg]

        response = await self._http.post("entries/create", data)
        return response["id"]
