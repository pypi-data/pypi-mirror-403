# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PitchCreateResponse"]


class PitchCreateResponse(BaseModel):
    pitch_id: Optional[str] = FieldInfo(alias="pitchId", default=None)

    status: Optional[str] = None
