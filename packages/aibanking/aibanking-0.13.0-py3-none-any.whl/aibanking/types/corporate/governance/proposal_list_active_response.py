# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["ProposalListActiveResponse", "Data"]


class Data(BaseModel):
    id: str

    required_approvals: int = FieldInfo(alias="requiredApprovals")

    status: Literal["PENDING", "APPROVED", "EXECUTED", "REJECTED"]

    title: str

    current_approvals: Optional[int] = FieldInfo(alias="currentApprovals", default=None)

    description: Optional[str] = None

    expires_at: Optional[datetime] = FieldInfo(alias="expiresAt", default=None)


class ProposalListActiveResponse(BaseModel):
    data: List[Data]
