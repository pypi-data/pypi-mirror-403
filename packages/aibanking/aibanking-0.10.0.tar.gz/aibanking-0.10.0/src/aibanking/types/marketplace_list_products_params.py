# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["MarketplaceListProductsParams"]


class MarketplaceListProductsParams(TypedDict, total=False):
    ai_personalization_level: Annotated[str, PropertyInfo(alias="aiPersonalizationLevel")]
    """Filter by AI personalization level (e.g., low, medium, high).

    'High' means highly relevant to user's specific needs.
    """

    category: str
    """
    Filter products by category (e.g., loans, insurance, credit_cards, investments).
    """

    limit: int
    """Maximum number of items to return in a single page."""

    min_rating: Annotated[int, PropertyInfo(alias="minRating")]
    """Minimum user rating for products (0-5)."""

    offset: int
    """Number of items to skip before starting to collect the result set."""
