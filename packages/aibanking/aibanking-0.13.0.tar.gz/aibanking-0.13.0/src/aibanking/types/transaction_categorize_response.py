# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

import datetime
from typing import Optional

from .._models import BaseModel

__all__ = ["TransactionCategorizeResponse"]


class TransactionCategorizeResponse(BaseModel):
    id: str

    amount: float

    currency: str

    date: datetime.date

    description: str

    category: Optional[str] = None

    notes: Optional[str] = None
