# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["ChatCreateResponse"]


class ChatCreateResponse(BaseModel):
    reply: Optional[str] = None

    session_id: Optional[str] = FieldInfo(alias="sessionId", default=None)

    suggested_actions: Optional[List[object]] = FieldInfo(alias="suggestedActions", default=None)
