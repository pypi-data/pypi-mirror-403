# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.investments import performance_get_historical_params
from ...types.investments.performance_get_historical_response import PerformanceGetHistoricalResponse

__all__ = ["PerformanceResource", "AsyncPerformanceResource"]


class PerformanceResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PerformanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return PerformanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PerformanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return PerformanceResourceWithStreamingResponse(self)

    def get_historical(
        self,
        *,
        range: Literal["1m", "3m", "1y", "5y", "max"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PerformanceGetHistoricalResponse:
        """
        Get Historical Performance Curves

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/investments/performance/historical",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"range": range}, performance_get_historical_params.PerformanceGetHistoricalParams
                ),
            ),
            cast_to=PerformanceGetHistoricalResponse,
        )


class AsyncPerformanceResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPerformanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncPerformanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPerformanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncPerformanceResourceWithStreamingResponse(self)

    async def get_historical(
        self,
        *,
        range: Literal["1m", "3m", "1y", "5y", "max"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PerformanceGetHistoricalResponse:
        """
        Get Historical Performance Curves

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/investments/performance/historical",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"range": range}, performance_get_historical_params.PerformanceGetHistoricalParams
                ),
            ),
            cast_to=PerformanceGetHistoricalResponse,
        )


class PerformanceResourceWithRawResponse:
    def __init__(self, performance: PerformanceResource) -> None:
        self._performance = performance

        self.get_historical = to_raw_response_wrapper(
            performance.get_historical,
        )


class AsyncPerformanceResourceWithRawResponse:
    def __init__(self, performance: AsyncPerformanceResource) -> None:
        self._performance = performance

        self.get_historical = async_to_raw_response_wrapper(
            performance.get_historical,
        )


class PerformanceResourceWithStreamingResponse:
    def __init__(self, performance: PerformanceResource) -> None:
        self._performance = performance

        self.get_historical = to_streamed_response_wrapper(
            performance.get_historical,
        )


class AsyncPerformanceResourceWithStreamingResponse:
    def __init__(self, performance: AsyncPerformanceResource) -> None:
        self._performance = performance

        self.get_historical = async_to_streamed_response_wrapper(
            performance.get_historical,
        )
