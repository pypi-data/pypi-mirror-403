# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["PitchCreateParams"]


class PitchCreateParams(TypedDict, total=False):
    business_plan: Required[Annotated[str, PropertyInfo(alias="businessPlan")]]
    """Full text of the concept"""

    financial_projections: Required[Annotated[object, PropertyInfo(alias="financialProjections")]]

    founding_team: Required[Annotated[Iterable[object], PropertyInfo(alias="foundingTeam")]]

    market_opportunity: Required[Annotated[str, PropertyInfo(alias="marketOpportunity")]]
