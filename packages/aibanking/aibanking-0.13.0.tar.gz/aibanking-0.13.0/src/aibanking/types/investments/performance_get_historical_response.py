# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from ..._models import BaseModel

__all__ = ["PerformanceGetHistoricalResponse"]


class PerformanceGetHistoricalResponse(BaseModel):
    benchmark_comparison: Optional[float] = FieldInfo(alias="benchmarkComparison", default=None)

    points: Optional[List[object]] = None
