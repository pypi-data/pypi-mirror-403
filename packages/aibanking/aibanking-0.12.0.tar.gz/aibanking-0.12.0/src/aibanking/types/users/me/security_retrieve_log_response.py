# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SecurityRetrieveLogResponse", "Data", "DataLocation"]


class DataLocation(BaseModel):
    city: Optional[str] = None

    country: Optional[str] = None

    latitude: Optional[float] = None

    longitude: Optional[float] = None


class Data(BaseModel):
    event: Optional[str] = None

    ip_address: Optional[str] = FieldInfo(alias="ipAddress", default=None)

    location: Optional[DataLocation] = None

    timestamp: Optional[datetime] = None


class SecurityRetrieveLogResponse(BaseModel):
    data: Optional[List[Data]] = None
