# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["MeUpdateParams", "Preferences"]


class MeUpdateParams(TypedDict, total=False):
    address: object

    preferences: Preferences
    """User's personalized preferences for the platform."""


class Preferences(TypedDict, total=False):
    """User's personalized preferences for the platform."""

    notification_channels: Annotated[object, PropertyInfo(alias="notificationChannels")]
    """Preferred channels for receiving notifications."""
