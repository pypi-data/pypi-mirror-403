# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["SimulateCreateParams"]


class SimulateCreateParams(TypedDict, total=False):
    prompt: Required[str]
    """Describe the financial scenario"""

    parameters: object
    """Key variables like duration, rate, or amount"""
