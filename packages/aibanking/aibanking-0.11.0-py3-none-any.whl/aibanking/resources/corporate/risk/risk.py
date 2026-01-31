# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from .fraud.fraud import (
    FraudResource,
    AsyncFraudResource,
    FraudResourceWithRawResponse,
    AsyncFraudResourceWithRawResponse,
    FraudResourceWithStreamingResponse,
    AsyncFraudResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.corporate import risk_run_stress_test_params
from ....types.corporate.risk_run_stress_test_response import RiskRunStressTestResponse
from ....types.corporate.risk_get_risk_exposure_response import RiskGetRiskExposureResponse

__all__ = ["RiskResource", "AsyncRiskResource"]


class RiskResource(SyncAPIResource):
    @cached_property
    def fraud(self) -> FraudResource:
        return FraudResource(self._client)

    @cached_property
    def with_raw_response(self) -> RiskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return RiskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RiskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return RiskResourceWithStreamingResponse(self)

    def get_risk_exposure(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RiskGetRiskExposureResponse:
        """Get Aggregate Risk Exposure"""
        return self._get(
            "/corporate/risk/exposure",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RiskGetRiskExposureResponse,
        )

    def run_stress_test(
        self,
        *,
        scenario_type: Literal["BANK_RUN", "MARKET_CRASH", "REGULATORY_SHOCK", "DEPEGGING"],
        intensity: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RiskRunStressTestResponse:
        """
        Simulates extreme market conditions (e.g., 2008 crash, hyperinflation) against
        the corporate ledger.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/risk/stress-test",
            body=maybe_transform(
                {
                    "scenario_type": scenario_type,
                    "intensity": intensity,
                },
                risk_run_stress_test_params.RiskRunStressTestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RiskRunStressTestResponse,
        )


class AsyncRiskResource(AsyncAPIResource):
    @cached_property
    def fraud(self) -> AsyncFraudResource:
        return AsyncFraudResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRiskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncRiskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRiskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncRiskResourceWithStreamingResponse(self)

    async def get_risk_exposure(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RiskGetRiskExposureResponse:
        """Get Aggregate Risk Exposure"""
        return await self._get(
            "/corporate/risk/exposure",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RiskGetRiskExposureResponse,
        )

    async def run_stress_test(
        self,
        *,
        scenario_type: Literal["BANK_RUN", "MARKET_CRASH", "REGULATORY_SHOCK", "DEPEGGING"],
        intensity: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RiskRunStressTestResponse:
        """
        Simulates extreme market conditions (e.g., 2008 crash, hyperinflation) against
        the corporate ledger.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/risk/stress-test",
            body=await async_maybe_transform(
                {
                    "scenario_type": scenario_type,
                    "intensity": intensity,
                },
                risk_run_stress_test_params.RiskRunStressTestParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RiskRunStressTestResponse,
        )


class RiskResourceWithRawResponse:
    def __init__(self, risk: RiskResource) -> None:
        self._risk = risk

        self.get_risk_exposure = to_raw_response_wrapper(
            risk.get_risk_exposure,
        )
        self.run_stress_test = to_raw_response_wrapper(
            risk.run_stress_test,
        )

    @cached_property
    def fraud(self) -> FraudResourceWithRawResponse:
        return FraudResourceWithRawResponse(self._risk.fraud)


class AsyncRiskResourceWithRawResponse:
    def __init__(self, risk: AsyncRiskResource) -> None:
        self._risk = risk

        self.get_risk_exposure = async_to_raw_response_wrapper(
            risk.get_risk_exposure,
        )
        self.run_stress_test = async_to_raw_response_wrapper(
            risk.run_stress_test,
        )

    @cached_property
    def fraud(self) -> AsyncFraudResourceWithRawResponse:
        return AsyncFraudResourceWithRawResponse(self._risk.fraud)


class RiskResourceWithStreamingResponse:
    def __init__(self, risk: RiskResource) -> None:
        self._risk = risk

        self.get_risk_exposure = to_streamed_response_wrapper(
            risk.get_risk_exposure,
        )
        self.run_stress_test = to_streamed_response_wrapper(
            risk.run_stress_test,
        )

    @cached_property
    def fraud(self) -> FraudResourceWithStreamingResponse:
        return FraudResourceWithStreamingResponse(self._risk.fraud)


class AsyncRiskResourceWithStreamingResponse:
    def __init__(self, risk: AsyncRiskResource) -> None:
        self._risk = risk

        self.get_risk_exposure = async_to_streamed_response_wrapper(
            risk.get_risk_exposure,
        )
        self.run_stress_test = async_to_streamed_response_wrapper(
            risk.run_stress_test,
        )

    @cached_property
    def fraud(self) -> AsyncFraudResourceWithStreamingResponse:
        return AsyncFraudResourceWithStreamingResponse(self._risk.fraud)
