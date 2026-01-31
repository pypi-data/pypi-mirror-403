# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["CorporateOnboardResponse"]


class CorporateOnboardResponse(BaseModel):
    corporate_id: Optional[str] = FieldInfo(alias="corporateId", default=None)

    status: Optional[str] = None
