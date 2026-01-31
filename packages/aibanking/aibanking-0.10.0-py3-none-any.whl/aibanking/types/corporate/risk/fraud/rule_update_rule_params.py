# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import TypedDict

__all__ = ["RuleUpdateRuleParams"]


class RuleUpdateRuleParams(TypedDict, total=False):
    action: object
    """Action to take when a fraud rule is triggered."""

    criteria: object
    """Criteria that define when a fraud rule should trigger."""
