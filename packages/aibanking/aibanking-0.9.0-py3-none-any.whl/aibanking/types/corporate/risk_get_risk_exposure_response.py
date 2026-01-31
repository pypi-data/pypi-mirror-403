# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["RiskGetRiskExposureResponse"]


class RiskGetRiskExposureResponse(BaseModel):
    asset_concentration: Optional[object] = FieldInfo(alias="assetConcentration", default=None)

    counterparty_risk: Optional[List[object]] = FieldInfo(alias="counterpartyRisk", default=None)

    value_at_risk: Optional[float] = FieldInfo(alias="valueAtRisk", default=None)
