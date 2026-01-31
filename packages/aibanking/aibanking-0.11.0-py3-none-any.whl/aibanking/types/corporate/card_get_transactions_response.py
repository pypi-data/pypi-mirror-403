# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import List, Optional

from ..._models import BaseModel

__all__ = ["CardGetTransactionsResponse", "Data"]


class Data(BaseModel):
    id: str

    amount: float

    currency: str

    date: datetime.date

    description: str

    category: Optional[str] = None

    notes: Optional[str] = None


class CardGetTransactionsResponse(BaseModel):
    data: Optional[List[Data]] = None
