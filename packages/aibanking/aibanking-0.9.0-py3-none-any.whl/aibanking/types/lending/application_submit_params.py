# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal, Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["ApplicationSubmitParams", "EmploymentData"]


class ApplicationSubmitParams(TypedDict, total=False):
    amount: Required[float]

    employment_data: Required[Annotated[EmploymentData, PropertyInfo(alias="employmentData")]]

    loan_type: Required[
        Annotated[Literal["MORTGAGE", "PERSONAL", "AUTO", "BUSINESS_EXPANSION"], PropertyInfo(alias="loanType")]
    ]

    term_months: Required[Annotated[int, PropertyInfo(alias="termMonths")]]

    assets: Iterable[object]

    collateral_id: Annotated[str, PropertyInfo(alias="collateralId")]

    liabilities: Iterable[object]


class EmploymentData(TypedDict, total=False):
    employer: Required[str]

    monthly_income: Required[Annotated[float, PropertyInfo(alias="monthlyIncome")]]

    tenure_months: Annotated[int, PropertyInfo(alias="tenureMonths")]
