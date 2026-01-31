# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["RiskRunStressTestParams"]


class RiskRunStressTestParams(TypedDict, total=False):
    scenario_type: Required[
        Annotated[
            Literal["BANK_RUN", "MARKET_CRASH", "REGULATORY_SHOCK", "DEPEGGING"], PropertyInfo(alias="scenarioType")
        ]
    ]

    intensity: float
