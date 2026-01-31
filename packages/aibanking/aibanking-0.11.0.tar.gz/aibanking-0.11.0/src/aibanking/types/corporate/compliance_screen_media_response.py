# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ComplianceScreenMediaResponse"]


class ComplianceScreenMediaResponse(BaseModel):
    negative_news_links: Optional[List[str]] = FieldInfo(alias="negativeNewsLinks", default=None)

    sentiment_score: Optional[float] = FieldInfo(alias="sentimentScore", default=None)
