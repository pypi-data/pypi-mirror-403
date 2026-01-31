# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from ..._models import BaseModel

__all__ = ["ModelFineTuneResponse"]


class ModelFineTuneResponse(BaseModel):
    job_id: Optional[str] = None
