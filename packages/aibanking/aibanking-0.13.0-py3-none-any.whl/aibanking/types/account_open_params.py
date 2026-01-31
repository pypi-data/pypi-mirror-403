# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["AccountOpenParams"]


class AccountOpenParams(TypedDict, total=False):
    currency: Required[str]

    initial_deposit: Required[Annotated[float, PropertyInfo(alias="initialDeposit")]]

    product_type: Required[
        Annotated[Literal["quantum_checking", "elite_savings", "high_yield_vault"], PropertyInfo(alias="productType")]
    ]

    owners: SequenceNotStr[str]
    """User IDs for joint accounts"""
