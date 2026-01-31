# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["TransactionSwapParams"]


class TransactionSwapParams(TypedDict, total=False):
    amount: Required[str]

    from_token: Required[Annotated[str, PropertyInfo(alias="fromToken")]]

    to_token: Required[Annotated[str, PropertyInfo(alias="toToken")]]
