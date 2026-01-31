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
from ...types.transactions import recurring_create_params
from ...types.transactions.recurring_list_response import RecurringListResponse

__all__ = ["RecurringResource", "AsyncRecurringResource"]


class RecurringResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RecurringResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return RecurringResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RecurringResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return RecurringResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        amount: float,
        category: str,
        frequency: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Manually Create Recurring Schedule

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/transactions/recurring",
            body=maybe_transform(
                {
                    "amount": amount,
                    "category": category,
                    "frequency": frequency,
                },
                recurring_create_params.RecurringCreateParams,
            ),
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
    ) -> RecurringListResponse:
        """List Detected Subscriptions"""
        return self._get(
            "/transactions/recurring",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RecurringListResponse,
        )

    def cancel(
        self,
        recurring_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Cancel Recurring Payment Detection

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not recurring_id:
            raise ValueError(f"Expected a non-empty value for `recurring_id` but received {recurring_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/transactions/recurring/{recurring_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncRecurringResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRecurringResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncRecurringResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRecurringResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncRecurringResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        amount: float,
        category: str,
        frequency: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Manually Create Recurring Schedule

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/transactions/recurring",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "category": category,
                    "frequency": frequency,
                },
                recurring_create_params.RecurringCreateParams,
            ),
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
    ) -> RecurringListResponse:
        """List Detected Subscriptions"""
        return await self._get(
            "/transactions/recurring",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RecurringListResponse,
        )

    async def cancel(
        self,
        recurring_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Cancel Recurring Payment Detection

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not recurring_id:
            raise ValueError(f"Expected a non-empty value for `recurring_id` but received {recurring_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/transactions/recurring/{recurring_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class RecurringResourceWithRawResponse:
    def __init__(self, recurring: RecurringResource) -> None:
        self._recurring = recurring

        self.create = to_raw_response_wrapper(
            recurring.create,
        )
        self.list = to_raw_response_wrapper(
            recurring.list,
        )
        self.cancel = to_raw_response_wrapper(
            recurring.cancel,
        )


class AsyncRecurringResourceWithRawResponse:
    def __init__(self, recurring: AsyncRecurringResource) -> None:
        self._recurring = recurring

        self.create = async_to_raw_response_wrapper(
            recurring.create,
        )
        self.list = async_to_raw_response_wrapper(
            recurring.list,
        )
        self.cancel = async_to_raw_response_wrapper(
            recurring.cancel,
        )


class RecurringResourceWithStreamingResponse:
    def __init__(self, recurring: RecurringResource) -> None:
        self._recurring = recurring

        self.create = to_streamed_response_wrapper(
            recurring.create,
        )
        self.list = to_streamed_response_wrapper(
            recurring.list,
        )
        self.cancel = to_streamed_response_wrapper(
            recurring.cancel,
        )


class AsyncRecurringResourceWithStreamingResponse:
    def __init__(self, recurring: AsyncRecurringResource) -> None:
        self._recurring = recurring

        self.create = async_to_streamed_response_wrapper(
            recurring.create,
        )
        self.list = async_to_streamed_response_wrapper(
            recurring.list,
        )
        self.cancel = async_to_streamed_response_wrapper(
            recurring.cancel,
        )
