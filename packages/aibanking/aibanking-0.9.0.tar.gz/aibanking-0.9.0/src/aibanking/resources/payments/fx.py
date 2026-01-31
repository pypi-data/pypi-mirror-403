# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union
from datetime import date

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
from ...types.payments import fx_book_deal_params, fx_get_rates_params, fx_execute_conversion_params
from ...types.payments.fx_get_rates_response import FxGetRatesResponse

__all__ = ["FxResource", "AsyncFxResource"]


class FxResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> FxResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return FxResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FxResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return FxResourceWithStreamingResponse(self)

    def book_deal(
        self,
        *,
        amount: float,
        pair: str,
        value_date: Union[str, date],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Book a Forward FX Deal

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/fx/deals",
            body=maybe_transform(
                {
                    "amount": amount,
                    "pair": pair,
                    "value_date": value_date,
                },
                fx_book_deal_params.FxBookDealParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def execute_conversion(
        self,
        *,
        amount: float,
        from_: str,
        to: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute Currency Conversion

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/fx/convert",
            body=maybe_transform(
                {
                    "amount": amount,
                    "from_": from_,
                    "to": to,
                },
                fx_execute_conversion_params.FxExecuteConversionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def get_rates(
        self,
        *,
        pair: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FxGetRatesResponse:
        """
        Market FX Rates

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/payments/fx/rates",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform({"pair": pair}, fx_get_rates_params.FxGetRatesParams),
            ),
            cast_to=FxGetRatesResponse,
        )


class AsyncFxResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncFxResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncFxResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFxResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncFxResourceWithStreamingResponse(self)

    async def book_deal(
        self,
        *,
        amount: float,
        pair: str,
        value_date: Union[str, date],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Book a Forward FX Deal

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/fx/deals",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "pair": pair,
                    "value_date": value_date,
                },
                fx_book_deal_params.FxBookDealParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def execute_conversion(
        self,
        *,
        amount: float,
        from_: str,
        to: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Execute Currency Conversion

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/fx/convert",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "from_": from_,
                    "to": to,
                },
                fx_execute_conversion_params.FxExecuteConversionParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def get_rates(
        self,
        *,
        pair: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FxGetRatesResponse:
        """
        Market FX Rates

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/payments/fx/rates",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform({"pair": pair}, fx_get_rates_params.FxGetRatesParams),
            ),
            cast_to=FxGetRatesResponse,
        )


class FxResourceWithRawResponse:
    def __init__(self, fx: FxResource) -> None:
        self._fx = fx

        self.book_deal = to_raw_response_wrapper(
            fx.book_deal,
        )
        self.execute_conversion = to_raw_response_wrapper(
            fx.execute_conversion,
        )
        self.get_rates = to_raw_response_wrapper(
            fx.get_rates,
        )


class AsyncFxResourceWithRawResponse:
    def __init__(self, fx: AsyncFxResource) -> None:
        self._fx = fx

        self.book_deal = async_to_raw_response_wrapper(
            fx.book_deal,
        )
        self.execute_conversion = async_to_raw_response_wrapper(
            fx.execute_conversion,
        )
        self.get_rates = async_to_raw_response_wrapper(
            fx.get_rates,
        )


class FxResourceWithStreamingResponse:
    def __init__(self, fx: FxResource) -> None:
        self._fx = fx

        self.book_deal = to_streamed_response_wrapper(
            fx.book_deal,
        )
        self.execute_conversion = to_streamed_response_wrapper(
            fx.execute_conversion,
        )
        self.get_rates = to_streamed_response_wrapper(
            fx.get_rates,
        )


class AsyncFxResourceWithStreamingResponse:
    def __init__(self, fx: AsyncFxResource) -> None:
        self._fx = fx

        self.book_deal = async_to_streamed_response_wrapper(
            fx.book_deal,
        )
        self.execute_conversion = async_to_streamed_response_wrapper(
            fx.execute_conversion,
        )
        self.get_rates = async_to_streamed_response_wrapper(
            fx.get_rates,
        )
