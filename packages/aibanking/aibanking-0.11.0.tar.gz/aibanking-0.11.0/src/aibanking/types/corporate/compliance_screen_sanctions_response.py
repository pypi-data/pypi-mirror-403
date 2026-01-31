# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ComplianceScreenSanctionsResponse"]


class ComplianceScreenSanctionsResponse(BaseModel):
    hits: Optional[List[object]] = None

    risk_level: Optional[Literal["Low", "Medium", "High", "Critical"]] = FieldInfo(alias="riskLevel", default=None)
