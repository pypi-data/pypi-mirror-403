# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime

from .._models import BaseModel

__all__ = ["SystemGetAuditLogsResponse", "Data"]


class Data(BaseModel):
    id: Optional[str] = None

    action: Optional[str] = None

    actor: Optional[str] = None

    impact: Optional[str] = None

    timestamp: Optional[datetime] = None


class SystemGetAuditLogsResponse(BaseModel):
    data: Optional[List[Data]] = None
