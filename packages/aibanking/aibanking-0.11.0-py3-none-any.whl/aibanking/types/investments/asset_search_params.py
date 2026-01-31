# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["AssetSearchParams"]


class AssetSearchParams(TypedDict, total=False):
    query: Required[str]

    asset_type: Annotated[Literal["EQUITY", "CRYPTO", "ETF", "BOND"], PropertyInfo(alias="assetType")]
