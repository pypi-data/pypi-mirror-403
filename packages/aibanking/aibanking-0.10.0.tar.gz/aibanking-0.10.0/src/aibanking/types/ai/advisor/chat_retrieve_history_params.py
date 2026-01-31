# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["ChatRetrieveHistoryParams"]


class ChatRetrieveHistoryParams(TypedDict, total=False):
    limit: int
    """Maximum number of items to return in a single page."""

    offset: int
    """Number of items to skip before starting to collect the result set."""

    session_id: Annotated[str, PropertyInfo(alias="sessionId")]
    """Optional: Filter history by a specific session ID.

    If omitted, recent conversations will be returned.
    """
