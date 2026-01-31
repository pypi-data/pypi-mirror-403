# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ComplianceScreenSanctionsParams", "Entity"]


class ComplianceScreenSanctionsParams(TypedDict, total=False):
    entities: Required[Iterable[Entity]]

    check_type: Annotated[Literal["standard", "enhanced_due_diligence"], PropertyInfo(alias="checkType")]


class Entity(TypedDict, total=False):
    country: str

    name: str
