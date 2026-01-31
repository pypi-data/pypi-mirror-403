# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Required, TypedDict

__all__ = ["TreasuryExecuteBulkPayoutsParams", "Payout"]


class TreasuryExecuteBulkPayoutsParams(TypedDict, total=False):
    payouts: Required[Iterable[Payout]]


class Payout(TypedDict, total=False):
    amount: float

    recipient_id: str
