# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["RiskRunStressTestResponse"]


class RiskRunStressTestResponse(BaseModel):
    ai_narrative: Optional[str] = FieldInfo(alias="aiNarrative", default=None)

    liquidity_gap: Optional[float] = FieldInfo(alias="liquidityGap", default=None)

    resilience_score: Optional[float] = FieldInfo(alias="resilienceScore", default=None)
