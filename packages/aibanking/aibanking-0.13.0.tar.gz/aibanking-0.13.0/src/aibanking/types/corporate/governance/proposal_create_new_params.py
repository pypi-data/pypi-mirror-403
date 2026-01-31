# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, Required, Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["ProposalCreateNewParams"]


class ProposalCreateNewParams(TypedDict, total=False):
    action_type: Required[
        Annotated[Literal["TRANSFER_LIMIT_CHANGE", "NEW_ADMIN", "LARGE_PAYMENT"], PropertyInfo(alias="actionType")]
    ]

    payload: Required[object]
    """The raw action data to be executed upon approval"""

    title: Required[str]

    description: str

    voting_period_hours: Annotated[int, PropertyInfo(alias="votingPeriodHours")]
