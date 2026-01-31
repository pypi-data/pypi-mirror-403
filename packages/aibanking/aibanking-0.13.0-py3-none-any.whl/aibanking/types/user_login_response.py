# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["UserLoginResponse"]


class UserLoginResponse(BaseModel):
    access_token: str = FieldInfo(alias="accessToken")

    expires_in: Optional[int] = FieldInfo(alias="expiresIn", default=None)

    refresh_token: Optional[str] = FieldInfo(alias="refreshToken", default=None)

    token_type: Optional[str] = FieldInfo(alias="tokenType", default=None)
