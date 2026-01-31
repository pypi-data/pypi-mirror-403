# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PredictionRetrieveInflationResponse"]


class PredictionRetrieveInflationResponse(BaseModel):
    confidence_score: Optional[int] = FieldInfo(alias="confidenceScore", default=None)

    forecasted_cpi: Optional[float] = FieldInfo(alias="forecastedCPI", default=None)

    period: Optional[str] = None
