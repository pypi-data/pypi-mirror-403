# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

from ..._types import SequenceNotStr

__all__ = ["WebhookRegisterParams"]


class WebhookRegisterParams(TypedDict, total=False):
    events: Required[SequenceNotStr[str]]

    url: Required[str]

    secret: str
    """HMAC signing secret"""
