# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date
from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ComplianceScreenPepParams"]


class ComplianceScreenPepParams(TypedDict, total=False):
    full_name: Required[Annotated[str, PropertyInfo(alias="fullName")]]

    dob: Annotated[Union[str, date], PropertyInfo(format="iso8601")]
