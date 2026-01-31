# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["DeviceListParams"]


class DeviceListParams(TypedDict, total=False):
    limit: int
    """Maximum number of items to return in a single page."""

    offset: int
    """Number of items to skip before starting to collect the result set."""
