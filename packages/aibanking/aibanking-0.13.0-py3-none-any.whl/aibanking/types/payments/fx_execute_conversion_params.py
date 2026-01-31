# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["FxExecuteConversionParams"]


class FxExecuteConversionParams(TypedDict, total=False):
    amount: Required[float]

    from_: Required[Annotated[str, PropertyInfo(alias="from")]]

    to: Required[str]
