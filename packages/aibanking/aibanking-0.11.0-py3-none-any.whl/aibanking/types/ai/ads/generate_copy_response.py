# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["GenerateCopyResponse"]


class GenerateCopyResponse(BaseModel):
    body_text: Optional[str] = FieldInfo(alias="bodyText", default=None)

    headlines: Optional[List[str]] = None
