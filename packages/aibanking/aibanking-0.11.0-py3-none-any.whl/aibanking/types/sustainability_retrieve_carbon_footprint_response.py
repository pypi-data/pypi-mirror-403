# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["SustainabilityRetrieveCarbonFootprintResponse", "Breakdown"]


class Breakdown(BaseModel):
    category: Optional[str] = None

    value: Optional[float] = None


class SustainabilityRetrieveCarbonFootprintResponse(BaseModel):
    period: str

    status: Literal["OPTIMAL", "HIGH_OUTPUT", "CRITICAL"]

    total_kg_co2e: float = FieldInfo(alias="totalKgCO2e")

    ai_recommendations: Optional[List[str]] = FieldInfo(alias="aiRecommendations", default=None)

    breakdown: Optional[List[Breakdown]] = None
