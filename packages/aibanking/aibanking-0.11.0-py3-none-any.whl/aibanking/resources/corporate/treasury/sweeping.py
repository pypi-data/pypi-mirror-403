# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ....types.corporate.treasury import sweeping_execute_sweep_params, sweeping_configure_rules_params

__all__ = ["SweepingResource", "AsyncSweepingResource"]


class SweepingResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SweepingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SweepingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SweepingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SweepingResourceWithStreamingResponse(self)

    def configure_rules(
        self,
        *,
        source_account: str,
        target_account: str,
        threshold: float,
        frequency: Literal["daily", "weekly", "monthly"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Configure Automated Cash Sweeping

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/corporate/treasury/sweeping/rules",
            body=maybe_transform(
                {
                    "source_account": source_account,
                    "target_account": target_account,
                    "threshold": threshold,
                    "frequency": frequency,
                },
                sweeping_configure_rules_params.SweepingConfigureRulesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def execute_sweep(
        self,
        *,
        rule_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Manual Sweep Trigger

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/corporate/treasury/sweeping/execute",
            body=maybe_transform({"rule_id": rule_id}, sweeping_execute_sweep_params.SweepingExecuteSweepParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncSweepingResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSweepingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSweepingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSweepingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSweepingResourceWithStreamingResponse(self)

    async def configure_rules(
        self,
        *,
        source_account: str,
        target_account: str,
        threshold: float,
        frequency: Literal["daily", "weekly", "monthly"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Configure Automated Cash Sweeping

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/corporate/treasury/sweeping/rules",
            body=await async_maybe_transform(
                {
                    "source_account": source_account,
                    "target_account": target_account,
                    "threshold": threshold,
                    "frequency": frequency,
                },
                sweeping_configure_rules_params.SweepingConfigureRulesParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def execute_sweep(
        self,
        *,
        rule_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Manual Sweep Trigger

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/corporate/treasury/sweeping/execute",
            body=await async_maybe_transform(
                {"rule_id": rule_id}, sweeping_execute_sweep_params.SweepingExecuteSweepParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class SweepingResourceWithRawResponse:
    def __init__(self, sweeping: SweepingResource) -> None:
        self._sweeping = sweeping

        self.configure_rules = to_raw_response_wrapper(
            sweeping.configure_rules,
        )
        self.execute_sweep = to_raw_response_wrapper(
            sweeping.execute_sweep,
        )


class AsyncSweepingResourceWithRawResponse:
    def __init__(self, sweeping: AsyncSweepingResource) -> None:
        self._sweeping = sweeping

        self.configure_rules = async_to_raw_response_wrapper(
            sweeping.configure_rules,
        )
        self.execute_sweep = async_to_raw_response_wrapper(
            sweeping.execute_sweep,
        )


class SweepingResourceWithStreamingResponse:
    def __init__(self, sweeping: SweepingResource) -> None:
        self._sweeping = sweeping

        self.configure_rules = to_streamed_response_wrapper(
            sweeping.configure_rules,
        )
        self.execute_sweep = to_streamed_response_wrapper(
            sweeping.execute_sweep,
        )


class AsyncSweepingResourceWithStreamingResponse:
    def __init__(self, sweeping: AsyncSweepingResource) -> None:
        self._sweeping = sweeping

        self.configure_rules = async_to_streamed_response_wrapper(
            sweeping.configure_rules,
        )
        self.execute_sweep = async_to_streamed_response_wrapper(
            sweeping.execute_sweep,
        )
