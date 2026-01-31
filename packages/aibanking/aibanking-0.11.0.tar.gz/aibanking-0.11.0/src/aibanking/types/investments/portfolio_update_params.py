# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["PortfolioUpdateParams"]


class PortfolioUpdateParams(TypedDict, total=False):
    risk_tolerance: Annotated[int, PropertyInfo(alias="riskTolerance")]

    strategy: str
