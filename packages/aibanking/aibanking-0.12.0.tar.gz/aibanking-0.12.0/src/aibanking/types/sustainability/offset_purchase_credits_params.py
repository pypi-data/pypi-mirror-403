# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["OffsetPurchaseCreditsParams"]


class OffsetPurchaseCreditsParams(TypedDict, total=False):
    project_id: Required[Annotated[str, PropertyInfo(alias="projectId")]]

    tonnes: Required[float]

    payment_source_id: Annotated[str, PropertyInfo(alias="paymentSourceId")]
