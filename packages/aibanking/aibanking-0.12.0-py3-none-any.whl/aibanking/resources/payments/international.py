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
from ...types.payments import international_execute_sepa_params, international_execute_swift_params
from ...types.payments.international_get_status_response import InternationalGetStatusResponse

__all__ = ["InternationalResource", "AsyncInternationalResource"]


class InternationalResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> InternationalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return InternationalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> InternationalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return InternationalResourceWithStreamingResponse(self)

    def execute_sepa(
        self,
        *,
        amount: float,
        iban: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        EU SEPA Credit Transfer

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/international/sepa",
            body=maybe_transform(
                {
                    "amount": amount,
                    "iban": iban,
                },
                international_execute_sepa_params.InternationalExecuteSepaParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def execute_swift(
        self,
        *,
        amount: float,
        bic: str,
        currency: str,
        iban: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Global SWIFT Transaction

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/payments/international/swift",
            body=maybe_transform(
                {
                    "amount": amount,
                    "bic": bic,
                    "currency": currency,
                    "iban": iban,
                },
                international_execute_swift_params.InternationalExecuteSwiftParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def get_status(
        self,
        payment_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InternationalGetStatusResponse:
        """
        Get international payment status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not payment_id:
            raise ValueError(f"Expected a non-empty value for `payment_id` but received {payment_id!r}")
        return self._get(
            f"/payments/international/{payment_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InternationalGetStatusResponse,
        )


class AsyncInternationalResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncInternationalResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncInternationalResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncInternationalResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncInternationalResourceWithStreamingResponse(self)

    async def execute_sepa(
        self,
        *,
        amount: float,
        iban: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        EU SEPA Credit Transfer

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/international/sepa",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "iban": iban,
                },
                international_execute_sepa_params.InternationalExecuteSepaParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def execute_swift(
        self,
        *,
        amount: float,
        bic: str,
        currency: str,
        iban: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Global SWIFT Transaction

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/payments/international/swift",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "bic": bic,
                    "currency": currency,
                    "iban": iban,
                },
                international_execute_swift_params.InternationalExecuteSwiftParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def get_status(
        self,
        payment_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InternationalGetStatusResponse:
        """
        Get international payment status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not payment_id:
            raise ValueError(f"Expected a non-empty value for `payment_id` but received {payment_id!r}")
        return await self._get(
            f"/payments/international/{payment_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InternationalGetStatusResponse,
        )


class InternationalResourceWithRawResponse:
    def __init__(self, international: InternationalResource) -> None:
        self._international = international

        self.execute_sepa = to_raw_response_wrapper(
            international.execute_sepa,
        )
        self.execute_swift = to_raw_response_wrapper(
            international.execute_swift,
        )
        self.get_status = to_raw_response_wrapper(
            international.get_status,
        )


class AsyncInternationalResourceWithRawResponse:
    def __init__(self, international: AsyncInternationalResource) -> None:
        self._international = international

        self.execute_sepa = async_to_raw_response_wrapper(
            international.execute_sepa,
        )
        self.execute_swift = async_to_raw_response_wrapper(
            international.execute_swift,
        )
        self.get_status = async_to_raw_response_wrapper(
            international.get_status,
        )


class InternationalResourceWithStreamingResponse:
    def __init__(self, international: InternationalResource) -> None:
        self._international = international

        self.execute_sepa = to_streamed_response_wrapper(
            international.execute_sepa,
        )
        self.execute_swift = to_streamed_response_wrapper(
            international.execute_swift,
        )
        self.get_status = to_streamed_response_wrapper(
            international.get_status,
        )


class AsyncInternationalResourceWithStreamingResponse:
    def __init__(self, international: AsyncInternationalResource) -> None:
        self._international = international

        self.execute_sepa = async_to_streamed_response_wrapper(
            international.execute_sepa,
        )
        self.execute_swift = async_to_streamed_response_wrapper(
            international.execute_swift,
        )
        self.get_status = async_to_streamed_response_wrapper(
            international.get_status,
        )
