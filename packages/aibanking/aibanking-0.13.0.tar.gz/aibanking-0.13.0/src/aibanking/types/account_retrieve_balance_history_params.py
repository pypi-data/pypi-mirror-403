# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["AccountRetrieveBalanceHistoryParams"]


class AccountRetrieveBalanceHistoryParams(TypedDict, total=False):
    period: Literal["1d", "7d", "30d", "1y", "all"]
