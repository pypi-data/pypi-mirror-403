"""Company models for the Canny SDK."""

from datetime import datetime
from typing import Any, Optional

from pydantic import Field

from .base import CannyModel


class Company(CannyModel):
    """A company in the Canny system.

    Attributes:
        id: A unique identifier for the company.
        created: Time at which the company was created.
        custom_fields: Custom fields associated with the company.
        domain: The company's domain.
        member_count: Number of users in the company.
        monthly_spend: The company's monthly spend.
        name: The company's name.
    """

    id: str
    created: datetime
    custom_fields: Optional[dict[str, Any]] = Field(default=None, alias="customFields")
    domain: Optional[str] = None
    member_count: Optional[int] = Field(default=None, alias="memberCount")
    monthly_spend: Optional[float] = Field(default=None, alias="monthlySpend")
    name: str


class CompanyListResponse(CannyModel):
    """Response from listing companies (v2 cursor-based pagination)."""

    companies: list[Company]
    has_next_page: bool = Field(alias="hasNextPage")
    cursor: Optional[str] = None
