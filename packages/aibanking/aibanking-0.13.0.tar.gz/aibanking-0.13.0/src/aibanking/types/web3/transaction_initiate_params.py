# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["TransactionInitiateParams"]


class TransactionInitiateParams(TypedDict, total=False):
    amount: Required[float]

    asset: Required[str]

    wallet_id: Required[str]
