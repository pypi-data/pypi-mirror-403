# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.ai.oracle.simulation_list_response import SimulationListResponse
from ....types.ai.oracle.simulation_retrieve_response import SimulationRetrieveResponse

__all__ = ["SimulationsResource", "AsyncSimulationsResource"]


class SimulationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SimulationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SimulationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SimulationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SimulationsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        simulation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationRetrieveResponse:
        """
        Get Specific Simulation Result

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not simulation_id:
            raise ValueError(f"Expected a non-empty value for `simulation_id` but received {simulation_id!r}")
        return self._get(
            f"/ai/oracle/simulations/{simulation_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulationRetrieveResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationListResponse:
        """List All Past Simulations"""
        return self._get(
            "/ai/oracle/simulations",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulationListResponse,
        )


class AsyncSimulationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSimulationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSimulationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSimulationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSimulationsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        simulation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationRetrieveResponse:
        """
        Get Specific Simulation Result

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not simulation_id:
            raise ValueError(f"Expected a non-empty value for `simulation_id` but received {simulation_id!r}")
        return await self._get(
            f"/ai/oracle/simulations/{simulation_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulationRetrieveResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationListResponse:
        """List All Past Simulations"""
        return await self._get(
            "/ai/oracle/simulations",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulationListResponse,
        )


class SimulationsResourceWithRawResponse:
    def __init__(self, simulations: SimulationsResource) -> None:
        self._simulations = simulations

        self.retrieve = to_raw_response_wrapper(
            simulations.retrieve,
        )
        self.list = to_raw_response_wrapper(
            simulations.list,
        )


class AsyncSimulationsResourceWithRawResponse:
    def __init__(self, simulations: AsyncSimulationsResource) -> None:
        self._simulations = simulations

        self.retrieve = async_to_raw_response_wrapper(
            simulations.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            simulations.list,
        )


class SimulationsResourceWithStreamingResponse:
    def __init__(self, simulations: SimulationsResource) -> None:
        self._simulations = simulations

        self.retrieve = to_streamed_response_wrapper(
            simulations.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            simulations.list,
        )


class AsyncSimulationsResourceWithStreamingResponse:
    def __init__(self, simulations: AsyncSimulationsResource) -> None:
        self._simulations = simulations

        self.retrieve = async_to_streamed_response_wrapper(
            simulations.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            simulations.list,
        )
