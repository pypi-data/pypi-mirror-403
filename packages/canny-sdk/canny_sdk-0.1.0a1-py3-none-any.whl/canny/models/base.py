"""Base Pydantic model configuration for Canny objects."""

from pydantic import BaseModel, ConfigDict


class CannyModel(BaseModel):
    """Base model for all Canny objects.

    Features:
    - Ignores unknown fields from API (forward compatibility)
    - Allows population by field name or alias
    - Strips whitespace from strings
    """

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        str_strip_whitespace=True,
    )
