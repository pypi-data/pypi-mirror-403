# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = ["TransactionInitiateDisputeParams"]


class TransactionInitiateDisputeParams(TypedDict, total=False):
    reason: Required[Literal["fraudulent", "duplicate", "incorrect_amount", "service_not_rendered"]]

    evidence_files: Annotated[SequenceNotStr[str], PropertyInfo(alias="evidenceFiles")]
    """URIs to evidence"""
