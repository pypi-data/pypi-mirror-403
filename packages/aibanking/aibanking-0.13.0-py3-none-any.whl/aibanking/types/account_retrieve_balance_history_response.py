# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["AccountRetrieveBalanceHistoryResponse", "History"]


class History(BaseModel):
    balance: Optional[float] = None

    timestamp: Optional[datetime] = None


class AccountRetrieveBalanceHistoryResponse(BaseModel):
    history: Optional[List[History]] = None
