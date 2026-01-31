# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["SystemGetStatusResponse"]


class SystemGetStatusResponse(BaseModel):
    active_nodes: Optional[int] = FieldInfo(alias="activeNodes", default=None)

    api_status: Optional[str] = FieldInfo(alias="apiStatus", default=None)

    gemini_uptime: Optional[str] = FieldInfo(alias="geminiUptime", default=None)

    mock_server_latency: Optional[int] = FieldInfo(alias="mockServerLatency", default=None)
