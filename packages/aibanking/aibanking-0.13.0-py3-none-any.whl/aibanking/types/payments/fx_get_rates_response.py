# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["FxGetRatesResponse"]


class FxGetRatesResponse(BaseModel):
    mid_rate: Optional[float] = FieldInfo(alias="midRate", default=None)

    timestamp: Optional[datetime] = None
