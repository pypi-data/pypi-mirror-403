# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .fx import (
    FxResource,
    AsyncFxResource,
    FxResourceWithRawResponse,
    AsyncFxResourceWithRawResponse,
    FxResourceWithStreamingResponse,
    AsyncFxResourceWithStreamingResponse,
)
from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from .domestic import (
    DomesticResource,
    AsyncDomesticResource,
    DomesticResourceWithRawResponse,
    AsyncDomesticResourceWithRawResponse,
    DomesticResourceWithStreamingResponse,
    AsyncDomesticResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .international import (
    InternationalResource,
    AsyncInternationalResource,
    InternationalResourceWithRawResponse,
    AsyncInternationalResourceWithRawResponse,
    InternationalResourceWithStreamingResponse,
    AsyncInternationalResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from ...types.payment_list_response import PaymentListResponse

__all__ = ["PaymentsResource", "AsyncPaymentsResource"]


class PaymentsResource(SyncAPIResource):
    @cached_property
    def domestic(self) -> DomesticResource:
        return DomesticResource(self._client)

    @cached_property
    def international(self) -> InternationalResource:
        return InternationalResource(self._client)

    @cached_property
    def fx(self) -> FxResource:
        return FxResource(self._client)

    @cached_property
    def with_raw_response(self) -> PaymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return PaymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PaymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return PaymentsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        payment_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get Payment Receipt

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not payment_id:
            raise ValueError(f"Expected a non-empty value for `payment_id` but received {payment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/payments/{payment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
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
    ) -> PaymentListResponse:
        """List Payment Activity"""
        return self._get(
            "/payments",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PaymentListResponse,
        )


class AsyncPaymentsResource(AsyncAPIResource):
    @cached_property
    def domestic(self) -> AsyncDomesticResource:
        return AsyncDomesticResource(self._client)

    @cached_property
    def international(self) -> AsyncInternationalResource:
        return AsyncInternationalResource(self._client)

    @cached_property
    def fx(self) -> AsyncFxResource:
        return AsyncFxResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncPaymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncPaymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPaymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncPaymentsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        payment_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get Payment Receipt

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not payment_id:
            raise ValueError(f"Expected a non-empty value for `payment_id` but received {payment_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/payments/{payment_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
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
    ) -> PaymentListResponse:
        """List Payment Activity"""
        return await self._get(
            "/payments",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PaymentListResponse,
        )


class PaymentsResourceWithRawResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments

        self.retrieve = to_raw_response_wrapper(
            payments.retrieve,
        )
        self.list = to_raw_response_wrapper(
            payments.list,
        )

    @cached_property
    def domestic(self) -> DomesticResourceWithRawResponse:
        return DomesticResourceWithRawResponse(self._payments.domestic)

    @cached_property
    def international(self) -> InternationalResourceWithRawResponse:
        return InternationalResourceWithRawResponse(self._payments.international)

    @cached_property
    def fx(self) -> FxResourceWithRawResponse:
        return FxResourceWithRawResponse(self._payments.fx)


class AsyncPaymentsResourceWithRawResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments

        self.retrieve = async_to_raw_response_wrapper(
            payments.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            payments.list,
        )

    @cached_property
    def domestic(self) -> AsyncDomesticResourceWithRawResponse:
        return AsyncDomesticResourceWithRawResponse(self._payments.domestic)

    @cached_property
    def international(self) -> AsyncInternationalResourceWithRawResponse:
        return AsyncInternationalResourceWithRawResponse(self._payments.international)

    @cached_property
    def fx(self) -> AsyncFxResourceWithRawResponse:
        return AsyncFxResourceWithRawResponse(self._payments.fx)


class PaymentsResourceWithStreamingResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments

        self.retrieve = to_streamed_response_wrapper(
            payments.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            payments.list,
        )

    @cached_property
    def domestic(self) -> DomesticResourceWithStreamingResponse:
        return DomesticResourceWithStreamingResponse(self._payments.domestic)

    @cached_property
    def international(self) -> InternationalResourceWithStreamingResponse:
        return InternationalResourceWithStreamingResponse(self._payments.international)

    @cached_property
    def fx(self) -> FxResourceWithStreamingResponse:
        return FxResourceWithStreamingResponse(self._payments.fx)


class AsyncPaymentsResourceWithStreamingResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments

        self.retrieve = async_to_streamed_response_wrapper(
            payments.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            payments.list,
        )

    @cached_property
    def domestic(self) -> AsyncDomesticResourceWithStreamingResponse:
        return AsyncDomesticResourceWithStreamingResponse(self._payments.domestic)

    @cached_property
    def international(self) -> AsyncInternationalResourceWithStreamingResponse:
        return AsyncInternationalResourceWithStreamingResponse(self._payments.international)

    @cached_property
    def fx(self) -> AsyncFxResourceWithStreamingResponse:
        return AsyncFxResourceWithStreamingResponse(self._payments.fx)
