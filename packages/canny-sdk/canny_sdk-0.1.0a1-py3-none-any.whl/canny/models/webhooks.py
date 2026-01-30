"""Webhook event models for the Canny SDK."""

from datetime import datetime
from typing import Any

from pydantic import Field

from .base import CannyModel


class WebhookEvent(CannyModel):
    """A webhook event from Canny.

    Attributes:
        created: Time at which the event was created.
        object: The object the event is about.
        object_type: The type of object (post, comment, vote).
        type: The type of event (e.g., post.created).
    """

    created: datetime
    object: dict[str, Any]
    object_type: str = Field(alias="objectType")
    type: str
