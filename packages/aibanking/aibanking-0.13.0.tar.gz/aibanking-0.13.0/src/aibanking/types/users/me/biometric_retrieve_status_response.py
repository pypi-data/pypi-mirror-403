# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["BiometricRetrieveStatusResponse"]


class BiometricRetrieveStatusResponse(BaseModel):
    biometrics_enrolled: Optional[bool] = FieldInfo(alias="biometricsEnrolled", default=None)

    last_used: Optional[datetime] = FieldInfo(alias="lastUsed", default=None)
