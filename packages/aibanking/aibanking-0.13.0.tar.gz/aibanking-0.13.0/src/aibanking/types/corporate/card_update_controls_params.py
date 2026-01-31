# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ..._types import SequenceNotStr
from ..._utils import PropertyInfo

__all__ = ["CardUpdateControlsParams"]


class CardUpdateControlsParams(TypedDict, total=False):
    allowed_categories: Annotated[SequenceNotStr[str], PropertyInfo(alias="allowedCategories")]

    geo_restriction: Annotated[SequenceNotStr[str], PropertyInfo(alias="geoRestriction")]

    monthly_limit: Annotated[float, PropertyInfo(alias="monthlyLimit")]
