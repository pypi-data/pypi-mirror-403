# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, TypedDict

__all__ = ["ContractDeployParams"]


class ContractDeployParams(TypedDict, total=False):
    abi: Required[object]

    bytecode: Required[str]
