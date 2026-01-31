# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["AnalysisCompetitorsResponse"]


class AnalysisCompetitorsResponse(BaseModel):
    competitors: Optional[List[object]] = None

    market_share_analysis: Optional[str] = FieldInfo(alias="marketShareAnalysis", default=None)
