# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ...._models import BaseModel

__all__ = ["SimulationListResponse", "Data"]


class Data(BaseModel):
    simulation_id: str = FieldInfo(alias="simulationId")

    status: str

    outcome_narrative: Optional[str] = FieldInfo(alias="outcomeNarrative", default=None)

    projected_value: Optional[float] = FieldInfo(alias="projectedValue", default=None)


class SimulationListResponse(BaseModel):
    data: Optional[List[Data]] = None
