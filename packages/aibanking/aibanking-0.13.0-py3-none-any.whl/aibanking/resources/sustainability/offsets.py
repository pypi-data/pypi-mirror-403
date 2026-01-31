# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
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
from ...types.sustainability import offset_retire_credits_params, offset_purchase_credits_params

__all__ = ["OffsetsResource", "AsyncOffsetsResource"]


class OffsetsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OffsetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return OffsetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OffsetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return OffsetsResourceWithStreamingResponse(self)

    def purchase_credits(
        self,
        *,
        project_id: str,
        tonnes: float,
        payment_source_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase Verified Carbon Credits

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/sustainability/offsets/purchase",
            body=maybe_transform(
                {
                    "project_id": project_id,
                    "tonnes": tonnes,
                    "payment_source_id": payment_source_id,
                },
                offset_purchase_credits_params.OffsetPurchaseCreditsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retire_credits(
        self,
        *,
        certificate_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Retire Carbon Credits (Permanent Offsetting)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/sustainability/offsets/retire",
            body=maybe_transform(
                {"certificate_id": certificate_id}, offset_retire_credits_params.OffsetRetireCreditsParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncOffsetsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOffsetsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncOffsetsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOffsetsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncOffsetsResourceWithStreamingResponse(self)

    async def purchase_credits(
        self,
        *,
        project_id: str,
        tonnes: float,
        payment_source_id: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Purchase Verified Carbon Credits

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/sustainability/offsets/purchase",
            body=await async_maybe_transform(
                {
                    "project_id": project_id,
                    "tonnes": tonnes,
                    "payment_source_id": payment_source_id,
                },
                offset_purchase_credits_params.OffsetPurchaseCreditsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retire_credits(
        self,
        *,
        certificate_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Retire Carbon Credits (Permanent Offsetting)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/sustainability/offsets/retire",
            body=await async_maybe_transform(
                {"certificate_id": certificate_id}, offset_retire_credits_params.OffsetRetireCreditsParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class OffsetsResourceWithRawResponse:
    def __init__(self, offsets: OffsetsResource) -> None:
        self._offsets = offsets

        self.purchase_credits = to_raw_response_wrapper(
            offsets.purchase_credits,
        )
        self.retire_credits = to_raw_response_wrapper(
            offsets.retire_credits,
        )


class AsyncOffsetsResourceWithRawResponse:
    def __init__(self, offsets: AsyncOffsetsResource) -> None:
        self._offsets = offsets

        self.purchase_credits = async_to_raw_response_wrapper(
            offsets.purchase_credits,
        )
        self.retire_credits = async_to_raw_response_wrapper(
            offsets.retire_credits,
        )


class OffsetsResourceWithStreamingResponse:
    def __init__(self, offsets: OffsetsResource) -> None:
        self._offsets = offsets

        self.purchase_credits = to_streamed_response_wrapper(
            offsets.purchase_credits,
        )
        self.retire_credits = to_streamed_response_wrapper(
            offsets.retire_credits,
        )


class AsyncOffsetsResourceWithStreamingResponse:
    def __init__(self, offsets: AsyncOffsetsResource) -> None:
        self._offsets = offsets

        self.purchase_credits = async_to_streamed_response_wrapper(
            offsets.purchase_credits,
        )
        self.retire_credits = async_to_streamed_response_wrapper(
            offsets.retire_credits,
        )
