# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["BiometricVerifyResponse"]


class BiometricVerifyResponse(BaseModel):
    verification_status: Optional[str] = FieldInfo(alias="verificationStatus", default=None)
