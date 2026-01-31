# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["GenerateCopyParams"]


class GenerateCopyParams(TypedDict, total=False):
    product_description: Required[Annotated[str, PropertyInfo(alias="productDescription")]]

    target_audience: Required[Annotated[str, PropertyInfo(alias="targetAudience")]]
