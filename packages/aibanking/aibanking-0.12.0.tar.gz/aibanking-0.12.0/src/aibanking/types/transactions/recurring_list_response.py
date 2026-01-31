# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["RecurringListResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    description: Optional[str] = None

    frequency: Optional[str] = None

    next_expected_date: Optional[date] = FieldInfo(alias="nextExpectedDate", default=None)


class RecurringListResponse(BaseModel):
    data: Optional[List[Data]] = None
