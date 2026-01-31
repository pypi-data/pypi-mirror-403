# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["DeviceListResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    os: Optional[str] = None

    trust_level: Optional[Literal["trusted", "untrusted"]] = FieldInfo(alias="trustLevel", default=None)

    type: Optional[str] = None


class DeviceListResponse(BaseModel):
    data: Optional[List[Data]] = None
