# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CardListAllResponse", "Data"]


class Data(BaseModel):
    id: str

    card_number_mask: str = FieldInfo(alias="cardNumberMask")

    holder_name: str = FieldInfo(alias="holderName")

    status: str

    frozen: Optional[bool] = None


class CardListAllResponse(BaseModel):
    data: Optional[List[Data]] = None

    total: Optional[int] = None
