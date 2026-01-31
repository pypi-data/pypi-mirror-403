# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PreferenceRetrieveResponse"]


class PreferenceRetrieveResponse(BaseModel):
    """User's personalized preferences for the platform."""

    notification_channels: Optional[object] = FieldInfo(alias="notificationChannels", default=None)
    """Preferred channels for receiving notifications."""
