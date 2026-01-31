# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import date

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["StatementListResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    issue_date: Optional[date] = FieldInfo(alias="issueDate", default=None)

    period: Optional[str] = None


class StatementListResponse(BaseModel):
    data: Optional[List[Data]] = None
