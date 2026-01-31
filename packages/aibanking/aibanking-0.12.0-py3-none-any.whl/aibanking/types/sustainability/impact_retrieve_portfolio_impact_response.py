# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ImpactRetrievePortfolioImpactResponse"]


class ImpactRetrievePortfolioImpactResponse(BaseModel):
    esg_score: Optional[int] = FieldInfo(alias="esgScore", default=None)

    fossil_fuel_exposure: Optional[float] = FieldInfo(alias="fossilFuelExposure", default=None)

    green_project_involvement: Optional[List[str]] = FieldInfo(alias="greenProjectInvolvement", default=None)

    social_justice_rating: Optional[str] = FieldInfo(alias="socialJusticeRating", default=None)
