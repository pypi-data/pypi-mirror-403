# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["PitchCreateParams"]


class PitchCreateParams(TypedDict, total=False):
    financial_projections: Required[Annotated[object, PropertyInfo(alias="financialProjections")]]
    """Key financial metrics and projections for the next 3-5 years."""
