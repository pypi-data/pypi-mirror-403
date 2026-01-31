# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["BiometricEnrollParams"]


class BiometricEnrollParams(TypedDict, total=False):
    biometric_type: Required[
        Annotated[Literal["fingerprint", "facial_recognition"], PropertyInfo(alias="biometricType")]
    ]

    signature: Required[str]
    """Public key or hash of signature"""
