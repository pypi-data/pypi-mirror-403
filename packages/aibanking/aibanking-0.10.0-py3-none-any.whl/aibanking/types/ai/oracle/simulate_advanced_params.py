# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["SimulateAdvancedParams"]


class SimulateAdvancedParams(TypedDict, total=False):
    global_economic_factors: Annotated[object, PropertyInfo(alias="globalEconomicFactors")]
    """Optional: Global economic conditions to apply to all scenarios."""

    personal_assumptions: Annotated[object, PropertyInfo(alias="personalAssumptions")]
    """Optional: Personal financial assumptions to override defaults."""
