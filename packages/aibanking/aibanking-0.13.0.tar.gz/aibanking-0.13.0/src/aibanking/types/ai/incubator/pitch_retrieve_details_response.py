# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PitchRetrieveDetailsResponse"]


class PitchRetrieveDetailsResponse(BaseModel):
    ai_feedback: Optional[str] = FieldInfo(alias="aiFeedback", default=None)

    funding_eligibility: Optional[bool] = FieldInfo(alias="fundingEligibility", default=None)
