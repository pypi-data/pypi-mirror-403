# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["CardIssueVirtualCardResponse"]


class CardIssueVirtualCardResponse(BaseModel):
    id: str

    card_number_mask: str = FieldInfo(alias="cardNumberMask")

    holder_name: str = FieldInfo(alias="holderName")

    status: str

    frozen: Optional[bool] = None
