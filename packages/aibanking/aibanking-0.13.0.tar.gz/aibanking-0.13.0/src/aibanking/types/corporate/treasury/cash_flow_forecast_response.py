# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["CashFlowForecastResponse"]


class CashFlowForecastResponse(BaseModel):
    ai_recommendations: Optional[List[str]] = FieldInfo(alias="aiRecommendations", default=None)

    forecast_id: Optional[str] = FieldInfo(alias="forecastId", default=None)

    projected_runway: Optional[int] = FieldInfo(alias="projectedRunway", default=None)
