# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["CardRequestPhysicalCardParams", "ShippingAddress"]


class CardRequestPhysicalCardParams(TypedDict, total=False):
    holder_name: Required[Annotated[str, PropertyInfo(alias="holderName")]]

    shipping_address: Required[Annotated[ShippingAddress, PropertyInfo(alias="shippingAddress")]]


class ShippingAddress(TypedDict, total=False):
    city: Required[str]

    country: Required[str]

    street: Required[str]

    state: str

    zip: str
