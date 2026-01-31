# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["StatementListResponse"]


class StatementListResponse(BaseModel):
    download_urls: object = FieldInfo(alias="downloadUrls")
    """Map of available download URLs for different formats."""
