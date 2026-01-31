# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["InternationalExecuteSwiftParams"]


class InternationalExecuteSwiftParams(TypedDict, total=False):
    amount: Required[float]

    bic: Required[str]

    currency: Required[str]

    iban: Required[str]
