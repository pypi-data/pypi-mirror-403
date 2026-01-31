# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["AccountOpenResponse"]


class AccountOpenResponse(BaseModel):
    id: str

    currency: str

    current_balance: float = FieldInfo(alias="currentBalance")

    institution_name: str = FieldInfo(alias="institutionName")

    type: str

    name: Optional[str] = None
