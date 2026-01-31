# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["MeRetrieveResponse", "Address", "SecurityStatus"]


class Address(BaseModel):
    city: str

    country: str

    street: str

    state: Optional[str] = None

    zip: Optional[str] = None


class SecurityStatus(BaseModel):
    last_login: Optional[datetime] = FieldInfo(alias="lastLogin", default=None)

    two_factor_enabled: Optional[bool] = FieldInfo(alias="twoFactorEnabled", default=None)


class MeRetrieveResponse(BaseModel):
    id: str

    email: str

    identity_verified: bool = FieldInfo(alias="identityVerified")

    name: str

    address: Optional[Address] = None

    preferences: Optional[object] = None

    security_status: Optional[SecurityStatus] = FieldInfo(alias="securityStatus", default=None)
