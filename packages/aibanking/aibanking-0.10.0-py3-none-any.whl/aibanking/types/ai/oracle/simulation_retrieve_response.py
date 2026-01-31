# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Union, Optional
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SimulationRetrieveResponse", "RiskAnalysis"]


class RiskAnalysis(BaseModel):
    risk_analysis: Optional[object] = FieldInfo(alias="riskAnalysis", default=None)
    """AI-driven risk assessment of the simulated scenario."""


SimulationRetrieveResponse: TypeAlias = Union[RiskAnalysis, object]
