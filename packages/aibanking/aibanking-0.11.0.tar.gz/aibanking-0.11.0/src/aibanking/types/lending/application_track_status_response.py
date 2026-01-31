# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["ApplicationTrackStatusResponse"]


class ApplicationTrackStatusResponse(BaseModel):
    status: Optional[str] = None

    underwriter_queue_pos: Optional[int] = FieldInfo(alias="underwriterQueuePos", default=None)
