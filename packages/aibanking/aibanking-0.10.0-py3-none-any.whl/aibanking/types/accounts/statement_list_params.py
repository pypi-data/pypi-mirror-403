# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["StatementListParams"]


class StatementListParams(TypedDict, total=False):
    format: str
    """Desired format for the statement.

    Use 'application/json' Accept header for download links.
    """

    month: int
    """Month for the statement (1-12)."""

    year: int
    """Year for the statement."""
