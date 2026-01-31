# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["NetworkGetStatusResponse"]


class NetworkGetStatusResponse(BaseModel):
    ethereum: Optional[object] = None

    polygon: Optional[object] = None

    solana: Optional[object] = None
