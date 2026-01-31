# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from ..._models import BaseModel

__all__ = ["CardUpdateControlsResponse"]


class CardUpdateControlsResponse(BaseModel):
    controls: object
    """Granular spending controls for a corporate card."""
