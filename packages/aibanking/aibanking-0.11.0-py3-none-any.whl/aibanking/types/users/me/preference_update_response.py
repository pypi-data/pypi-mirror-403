# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PreferenceUpdateResponse"]


class PreferenceUpdateResponse(BaseModel):
    ai_interaction_mode: Optional[str] = FieldInfo(alias="aiInteractionMode", default=None)

    theme: Optional[str] = None
