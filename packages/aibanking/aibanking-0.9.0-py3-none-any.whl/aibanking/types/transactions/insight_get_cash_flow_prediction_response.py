# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["InsightGetCashFlowPredictionResponse"]


class InsightGetCashFlowPredictionResponse(BaseModel):
    forecast_days: Optional[int] = FieldInfo(alias="forecastDays", default=None)

    projected_low_point: Optional[float] = FieldInfo(alias="projectedLowPoint", default=None)

    recommendations: Optional[List[str]] = None
