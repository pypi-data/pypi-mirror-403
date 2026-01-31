# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UserRegisterResponse", "Preferences"]


class Preferences(BaseModel):
    """User's personalized preferences for the platform."""

    notification_channels: Optional[object] = FieldInfo(alias="notificationChannels", default=None)
    """Preferred channels for receiving notifications."""


class UserRegisterResponse(BaseModel):
    address: Optional[object] = None

    preferences: Optional[Preferences] = None
    """User's personalized preferences for the platform."""

    security_status: Optional[object] = FieldInfo(alias="securityStatus", default=None)
    """Security-related status for the user account."""
