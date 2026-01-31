# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TransactionCategorizeResponse", "MerchantDetails"]


class MerchantDetails(BaseModel):
    """Detailed information about a merchant associated with a transaction."""

    address: Optional[object] = None


class TransactionCategorizeResponse(BaseModel):
    location: Optional[object] = None
    """Geographic location details for a transaction."""

    merchant_details: Optional[MerchantDetails] = FieldInfo(alias="merchantDetails", default=None)
    """Detailed information about a merchant associated with a transaction."""
