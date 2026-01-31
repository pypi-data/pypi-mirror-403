# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.ai.oracle import simulate_create_params, simulate_advanced_params, simulate_monte_carlo_params
from ....types.ai.oracle.simulate_create_response import SimulateCreateResponse
from ....types.ai.oracle.simulate_advanced_response import SimulateAdvancedResponse

__all__ = ["SimulateResource", "AsyncSimulateResource"]


class SimulateResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SimulateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SimulateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SimulateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SimulateResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        prompt: str,
        parameters: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateCreateResponse:
        """
        Run a 'What-If' Financial Simulation (Standard)

        Args:
          prompt: Describe the financial scenario

          parameters: Key variables like duration, rate, or amount

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/oracle/simulate",
            body=maybe_transform(
                {
                    "prompt": prompt,
                    "parameters": parameters,
                },
                simulate_create_params.SimulateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateCreateResponse,
        )

    def advanced(
        self,
        *,
        prompt: str,
        scenarios: Iterable[simulate_advanced_params.Scenario],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateAdvancedResponse:
        """
        run Advanced Simulation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/oracle/simulate/advanced",
            body=maybe_transform(
                {
                    "prompt": prompt,
                    "scenarios": scenarios,
                },
                simulate_advanced_params.SimulateAdvancedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateAdvancedResponse,
        )

    def monte_carlo(
        self,
        *,
        iterations: int,
        variables: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        run Monte Carlo Simulation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/ai/oracle/simulate/monte-carlo",
            body=maybe_transform(
                {
                    "iterations": iterations,
                    "variables": variables,
                },
                simulate_monte_carlo_params.SimulateMonteCarloParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncSimulateResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSimulateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSimulateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSimulateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSimulateResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        prompt: str,
        parameters: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateCreateResponse:
        """
        Run a 'What-If' Financial Simulation (Standard)

        Args:
          prompt: Describe the financial scenario

          parameters: Key variables like duration, rate, or amount

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/oracle/simulate",
            body=await async_maybe_transform(
                {
                    "prompt": prompt,
                    "parameters": parameters,
                },
                simulate_create_params.SimulateCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateCreateResponse,
        )

    async def advanced(
        self,
        *,
        prompt: str,
        scenarios: Iterable[simulate_advanced_params.Scenario],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateAdvancedResponse:
        """
        run Advanced Simulation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/oracle/simulate/advanced",
            body=await async_maybe_transform(
                {
                    "prompt": prompt,
                    "scenarios": scenarios,
                },
                simulate_advanced_params.SimulateAdvancedParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateAdvancedResponse,
        )

    async def monte_carlo(
        self,
        *,
        iterations: int,
        variables: SequenceNotStr[str],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        run Monte Carlo Simulation

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/ai/oracle/simulate/monte-carlo",
            body=await async_maybe_transform(
                {
                    "iterations": iterations,
                    "variables": variables,
                },
                simulate_monte_carlo_params.SimulateMonteCarloParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class SimulateResourceWithRawResponse:
    def __init__(self, simulate: SimulateResource) -> None:
        self._simulate = simulate

        self.create = to_raw_response_wrapper(
            simulate.create,
        )
        self.advanced = to_raw_response_wrapper(
            simulate.advanced,
        )
        self.monte_carlo = to_raw_response_wrapper(
            simulate.monte_carlo,
        )


class AsyncSimulateResourceWithRawResponse:
    def __init__(self, simulate: AsyncSimulateResource) -> None:
        self._simulate = simulate

        self.create = async_to_raw_response_wrapper(
            simulate.create,
        )
        self.advanced = async_to_raw_response_wrapper(
            simulate.advanced,
        )
        self.monte_carlo = async_to_raw_response_wrapper(
            simulate.monte_carlo,
        )


class SimulateResourceWithStreamingResponse:
    def __init__(self, simulate: SimulateResource) -> None:
        self._simulate = simulate

        self.create = to_streamed_response_wrapper(
            simulate.create,
        )
        self.advanced = to_streamed_response_wrapper(
            simulate.advanced,
        )
        self.monte_carlo = to_streamed_response_wrapper(
            simulate.monte_carlo,
        )


class AsyncSimulateResourceWithStreamingResponse:
    def __init__(self, simulate: AsyncSimulateResource) -> None:
        self._simulate = simulate

        self.create = async_to_streamed_response_wrapper(
            simulate.create,
        )
        self.advanced = async_to_streamed_response_wrapper(
            simulate.advanced,
        )
        self.monte_carlo = async_to_streamed_response_wrapper(
            simulate.monte_carlo,
        )
