# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["GenerateVideoParams"]


class GenerateVideoParams(TypedDict, total=False):
    length_seconds: Required[Annotated[Literal[15, 30, 60], PropertyInfo(alias="lengthSeconds")]]

    prompt: Required[str]
    """Visual description"""

    style: Required[Literal["Cinematic", "Minimalist", "Cyberpunk", "Professional"]]
