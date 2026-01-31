# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
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
from ...types.payments import domestic_execute_ach_params, domestic_execute_rtp_params, domestic_execute_wire_params

__all__ = ["DomesticResource", "AsyncDomesticResource"]


class DomesticResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DomesticResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return DomesticResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DomesticResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return DomesticResourceWithStreamingResponse(self)

    def execute_ach(
        self,
        *,
        account: str,
        amount: float,
        routing: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute ACH Transfer

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/domestic/ach",
            body=maybe_transform(
                {
                    "account": account,
                    "amount": amount,
                    "routing": routing,
                },
                domestic_execute_ach_params.DomesticExecuteACHParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def execute_rtp(
        self,
        *,
        amount: float,
        recipient_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Real-time Payment (RTP)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/domestic/rtp",
            body=maybe_transform(
                {
                    "amount": amount,
                    "recipient_id": recipient_id,
                },
                domestic_execute_rtp_params.DomesticExecuteRtpParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def execute_wire(
        self,
        *,
        account: str,
        amount: float,
        routing: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute Federal Wire

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/domestic/wire",
            body=maybe_transform(
                {
                    "account": account,
                    "amount": amount,
                    "routing": routing,
                },
                domestic_execute_wire_params.DomesticExecuteWireParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncDomesticResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDomesticResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncDomesticResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDomesticResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncDomesticResourceWithStreamingResponse(self)

    async def execute_ach(
        self,
        *,
        account: str,
        amount: float,
        routing: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute ACH Transfer

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/domestic/ach",
            body=await async_maybe_transform(
                {
                    "account": account,
                    "amount": amount,
                    "routing": routing,
                },
                domestic_execute_ach_params.DomesticExecuteACHParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def execute_rtp(
        self,
        *,
        amount: float,
        recipient_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Real-time Payment (RTP)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/domestic/rtp",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "recipient_id": recipient_id,
                },
                domestic_execute_rtp_params.DomesticExecuteRtpParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def execute_wire(
        self,
        *,
        account: str,
        amount: float,
        routing: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute Federal Wire

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/domestic/wire",
            body=await async_maybe_transform(
                {
                    "account": account,
                    "amount": amount,
                    "routing": routing,
                },
                domestic_execute_wire_params.DomesticExecuteWireParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class DomesticResourceWithRawResponse:
    def __init__(self, domestic: DomesticResource) -> None:
        self._domestic = domestic

        self.execute_ach = to_raw_response_wrapper(
            domestic.execute_ach,
        )
        self.execute_rtp = to_raw_response_wrapper(
            domestic.execute_rtp,
        )
        self.execute_wire = to_raw_response_wrapper(
            domestic.execute_wire,
        )


class AsyncDomesticResourceWithRawResponse:
    def __init__(self, domestic: AsyncDomesticResource) -> None:
        self._domestic = domestic

        self.execute_ach = async_to_raw_response_wrapper(
            domestic.execute_ach,
        )
        self.execute_rtp = async_to_raw_response_wrapper(
            domestic.execute_rtp,
        )
        self.execute_wire = async_to_raw_response_wrapper(
            domestic.execute_wire,
        )


class DomesticResourceWithStreamingResponse:
    def __init__(self, domestic: DomesticResource) -> None:
        self._domestic = domestic

        self.execute_ach = to_streamed_response_wrapper(
            domestic.execute_ach,
        )
        self.execute_rtp = to_streamed_response_wrapper(
            domestic.execute_rtp,
        )
        self.execute_wire = to_streamed_response_wrapper(
            domestic.execute_wire,
        )


class AsyncDomesticResourceWithStreamingResponse:
    def __init__(self, domestic: AsyncDomesticResource) -> None:
        self._domestic = domestic

        self.execute_ach = async_to_streamed_response_wrapper(
            domestic.execute_ach,
        )
        self.execute_rtp = async_to_streamed_response_wrapper(
            domestic.execute_rtp,
        )
        self.execute_wire = async_to_streamed_response_wrapper(
            domestic.execute_wire,
        )
