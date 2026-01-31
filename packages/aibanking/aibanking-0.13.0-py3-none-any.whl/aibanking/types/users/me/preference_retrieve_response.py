# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["PreferenceRetrieveResponse"]


class PreferenceRetrieveResponse(BaseModel):
    ai_interaction_mode: Optional[Literal["proactive", "reactive", "silent"]] = FieldInfo(
        alias="aiInteractionMode", default=None
    )

    data_sharing_consent: Optional[bool] = FieldInfo(alias="dataSharingConsent", default=None)

    preferred_language: Optional[str] = FieldInfo(alias="preferredLanguage", default=None)

    theme: Optional[str] = None
