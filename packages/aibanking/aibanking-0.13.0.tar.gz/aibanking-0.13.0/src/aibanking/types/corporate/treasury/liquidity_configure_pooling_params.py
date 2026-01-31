# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

from ...._types import SequenceNotStr

__all__ = ["LiquidityConfigurePoolingParams"]


class LiquidityConfigurePoolingParams(TypedDict, total=False):
    source_account_ids: SequenceNotStr[str]

    target_account_id: str
