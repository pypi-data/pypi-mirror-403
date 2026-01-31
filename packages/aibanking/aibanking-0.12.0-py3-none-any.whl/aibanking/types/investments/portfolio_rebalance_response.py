# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["PortfolioRebalanceResponse"]


class PortfolioRebalanceResponse(BaseModel):
    impact_summary: Optional[str] = FieldInfo(alias="impactSummary", default=None)

    rebalance_id: Optional[str] = FieldInfo(alias="rebalanceId", default=None)
