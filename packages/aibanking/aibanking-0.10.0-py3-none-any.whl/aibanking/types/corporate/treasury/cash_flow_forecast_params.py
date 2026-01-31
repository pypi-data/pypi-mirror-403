# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Annotated, TypedDict

from ...._utils import PropertyInfo

__all__ = ["CashFlowForecastParams"]


class CashFlowForecastParams(TypedDict, total=False):
    forecast_horizon_days: Annotated[int, PropertyInfo(alias="forecastHorizonDays")]
    """
    The number of days into the future for which to generate the cash flow forecast
    (e.g., 30, 90, 180).
    """

    include_scenario_analysis: Annotated[bool, PropertyInfo(alias="includeScenarioAnalysis")]
    """
    If true, the forecast will include best-case and worst-case scenario analysis
    alongside the most likely projection.
    """
