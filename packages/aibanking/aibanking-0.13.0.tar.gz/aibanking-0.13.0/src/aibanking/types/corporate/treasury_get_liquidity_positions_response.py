# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from ..._models import BaseModel

__all__ = ["TreasuryGetLiquidityPositionsResponse"]


class TreasuryGetLiquidityPositionsResponse(BaseModel):
    positions: Optional[List[object]] = None

    total_liquidity: Optional[float] = None
