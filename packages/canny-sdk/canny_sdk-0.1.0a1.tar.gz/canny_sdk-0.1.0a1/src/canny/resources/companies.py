"""Companies resource for the Canny SDK."""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from ..models.companies import Company, CompanyListResponse
from ..pagination import CursorPaginator
from .base import BaseAsyncResource, BaseResource


class CompaniesResource(BaseResource):
    """Companies API endpoints.

    Companies are organizations associated with users.
    """

    def list(
        self,
        *,
        search: str | None = None,
        segment: str | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> CompanyListResponse:
        """List companies with optional filtering (v2 cursor-based pagination).

        Args:
            search: Search by company name.
            segment: Filter by segment URL name.
            limit: Number of companies to return (1-100).
            cursor: Cursor for pagination.

        Returns:
            A response containing the list of companies.
        """
        data: dict[str, Any] = {"limit": limit}
        if search:
            data["search"] = search
        if segment:
            data["segment"] = segment
        if cursor:
            data["cursor"] = cursor

        response = self._http.post("companies/list", data, api_version=2)
        return CompanyListResponse.model_validate(response)

    def list_all(self, **kwargs: Any) -> Iterator[Company]:
        """Iterate over all companies with automatic pagination.

        Returns:
            An iterator over all companies.
        """
        return CursorPaginator(
            fetch_fn=self.list,
            items_key="companies",
            **kwargs,
        )

    # Write operations

    def update(
        self,
        *,
        id: str,
        custom_fields: dict[str, Any] | None = None,
        monthly_spend: float | None = None,
        name: str | None = None,
    ) -> None:
        """Update a company.

        Args:
            id: The unique identifier of the company.
            custom_fields: Custom fields to update.
            monthly_spend: The company's monthly spend.
            name: The company's name.
        """
        self._check_write_allowed("update company")

        data: dict[str, Any] = {"id": id}
        if custom_fields is not None:
            data["customFields"] = custom_fields
        if monthly_spend is not None:
            data["monthlySpend"] = monthly_spend
        if name is not None:
            data["name"] = name

        self._http.post("companies/update", data)

    def delete(self, *, id: str) -> None:
        """Delete a company.

        Args:
            id: The unique identifier of the company.
        """
        self._check_write_allowed("delete company")
        self._http.post("companies/delete", {"id": id})


class CompaniesAsyncResource(BaseAsyncResource):
    """Async Companies API endpoints."""

    async def list(
        self,
        *,
        search: str | None = None,
        segment: str | None = None,
        limit: int = 10,
        cursor: str | None = None,
    ) -> CompanyListResponse:
        """List companies with optional filtering."""
        data: dict[str, Any] = {"limit": limit}
        if search:
            data["search"] = search
        if segment:
            data["segment"] = segment
        if cursor:
            data["cursor"] = cursor

        response = await self._http.post("companies/list", data, api_version=2)
        return CompanyListResponse.model_validate(response)

    async def update(
        self,
        *,
        id: str,
        custom_fields: dict[str, Any] | None = None,
        monthly_spend: float | None = None,
        name: str | None = None,
    ) -> None:
        """Update a company."""
        self._check_write_allowed("update company")

        data: dict[str, Any] = {"id": id}
        if custom_fields is not None:
            data["customFields"] = custom_fields
        if monthly_spend is not None:
            data["monthlySpend"] = monthly_spend
        if name is not None:
            data["name"] = name

        await self._http.post("companies/update", data)

    async def delete(self, *, id: str) -> None:
        """Delete a company."""
        self._check_write_allowed("delete company")
        await self._http.post("companies/delete", {"id": id})
