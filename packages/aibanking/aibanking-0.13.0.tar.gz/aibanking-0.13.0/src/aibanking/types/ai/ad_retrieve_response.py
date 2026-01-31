# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["AdRetrieveResponse"]


class AdRetrieveResponse(BaseModel):
    progress: Optional[int] = None

    status: Optional[str] = None

    video_uri: Optional[str] = FieldInfo(alias="videoUri", default=None)
