# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
from ....types.corporate.treasury import liquidity_optimize_params, liquidity_configure_pooling_params
from ....types.corporate.treasury.liquidity_optimize_response import LiquidityOptimizeResponse

__all__ = ["LiquidityResource", "AsyncLiquidityResource"]


class LiquidityResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> LiquidityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return LiquidityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LiquidityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return LiquidityResourceWithStreamingResponse(self)

    def configure_pooling(
        self,
        *,
        source_account_ids: SequenceNotStr[str] | Omit = omit,
        target_account_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Configure liquidity pooling

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/corporate/treasury/liquidity/pooling",
            body=maybe_transform(
                {
                    "source_account_ids": source_account_ids,
                    "target_account_id": target_account_id,
                },
                liquidity_configure_pooling_params.LiquidityConfigurePoolingParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def optimize(
        self,
        *,
        sweep_excess: bool | Omit = omit,
        target_reserve: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LiquidityOptimizeResponse:
        """
        AI Liquidity Optimization Engine

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/treasury/liquidity/optimize",
            body=maybe_transform(
                {
                    "sweep_excess": sweep_excess,
                    "target_reserve": target_reserve,
                },
                liquidity_optimize_params.LiquidityOptimizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LiquidityOptimizeResponse,
        )


class AsyncLiquidityResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncLiquidityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncLiquidityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLiquidityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncLiquidityResourceWithStreamingResponse(self)

    async def configure_pooling(
        self,
        *,
        source_account_ids: SequenceNotStr[str] | Omit = omit,
        target_account_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Configure liquidity pooling

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/corporate/treasury/liquidity/pooling",
            body=await async_maybe_transform(
                {
                    "source_account_ids": source_account_ids,
                    "target_account_id": target_account_id,
                },
                liquidity_configure_pooling_params.LiquidityConfigurePoolingParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def optimize(
        self,
        *,
        sweep_excess: bool | Omit = omit,
        target_reserve: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> LiquidityOptimizeResponse:
        """
        AI Liquidity Optimization Engine

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/treasury/liquidity/optimize",
            body=await async_maybe_transform(
                {
                    "sweep_excess": sweep_excess,
                    "target_reserve": target_reserve,
                },
                liquidity_optimize_params.LiquidityOptimizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=LiquidityOptimizeResponse,
        )


class LiquidityResourceWithRawResponse:
    def __init__(self, liquidity: LiquidityResource) -> None:
        self._liquidity = liquidity

        self.configure_pooling = to_raw_response_wrapper(
            liquidity.configure_pooling,
        )
        self.optimize = to_raw_response_wrapper(
            liquidity.optimize,
        )


class AsyncLiquidityResourceWithRawResponse:
    def __init__(self, liquidity: AsyncLiquidityResource) -> None:
        self._liquidity = liquidity

        self.configure_pooling = async_to_raw_response_wrapper(
            liquidity.configure_pooling,
        )
        self.optimize = async_to_raw_response_wrapper(
            liquidity.optimize,
        )


class LiquidityResourceWithStreamingResponse:
    def __init__(self, liquidity: LiquidityResource) -> None:
        self._liquidity = liquidity

        self.configure_pooling = to_streamed_response_wrapper(
            liquidity.configure_pooling,
        )
        self.optimize = to_streamed_response_wrapper(
            liquidity.optimize,
        )


class AsyncLiquidityResourceWithStreamingResponse:
    def __init__(self, liquidity: AsyncLiquidityResource) -> None:
        self._liquidity = liquidity

        self.configure_pooling = async_to_streamed_response_wrapper(
            liquidity.configure_pooling,
        )
        self.optimize = async_to_streamed_response_wrapper(
            liquidity.optimize,
        )
