# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["PasswordResetConfirmParams"]


class PasswordResetConfirmParams(TypedDict, total=False):
    identifier: Required[str]

    new_password: Required[Annotated[str, PropertyInfo(alias="newPassword")]]

    verification_code: Required[Annotated[str, PropertyInfo(alias="verificationCode")]]
    """The 6-digit code sent to user"""
