# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PredictionRetrieveMarketCrashProbabilityResponse"]


class PredictionRetrieveMarketCrashProbabilityResponse(BaseModel):
    ai_narrative: Optional[str] = FieldInfo(alias="aiNarrative", default=None)

    crash_probability: Optional[float] = FieldInfo(alias="crashProbability", default=None)

    risk_factors: Optional[List[str]] = FieldInfo(alias="riskFactors", default=None)
