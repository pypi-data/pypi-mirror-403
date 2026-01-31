# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SimulateAdvancedResponse"]


class SimulateAdvancedResponse(BaseModel):
    simulation_id: str = FieldInfo(alias="simulationId")

    status: str

    outcome_narrative: Optional[str] = FieldInfo(alias="outcomeNarrative", default=None)

    projected_value: Optional[float] = FieldInfo(alias="projectedValue", default=None)
