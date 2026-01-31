# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["AgentRetrieveCapabilitiesResponse", "Data"]


class Data(BaseModel):
    description: Optional[str] = None

    enabled: Optional[bool] = None

    name: Optional[str] = None

    requires_human_approval: Optional[bool] = FieldInfo(alias="requiresHumanApproval", default=None)


class AgentRetrieveCapabilitiesResponse(BaseModel):
    data: Optional[List[Data]] = None
