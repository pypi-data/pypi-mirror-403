# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AssetSearchParams"]


class AssetSearchParams(TypedDict, total=False):
    limit: int
    """Maximum number of items to return in a single page."""

    min_esg_score: Annotated[int, PropertyInfo(alias="minESGScore")]
    """Minimum desired ESG score (0-10)."""

    offset: int
    """Number of items to skip before starting to collect the result set."""

    query: str
    """Search query for asset name or symbol."""
