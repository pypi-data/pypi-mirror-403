# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["FraudAnalyzeTransactionResponse"]


class FraudAnalyzeTransactionResponse(BaseModel):
    decision: Optional[Literal["APPROVE", "FLAG", "BLOCK"]] = None

    risk_score: Optional[int] = FieldInfo(alias="riskScore", default=None)
