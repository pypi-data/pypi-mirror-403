# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.marketplace.offer_list_offers_response import OfferListOffersResponse

__all__ = ["OffersResource", "AsyncOffersResource"]


class OffersResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OffersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return OffersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OffersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return OffersResourceWithStreamingResponse(self)

    def list_offers(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OfferListOffersResponse:
        """List AI-Targeted Loyalty Offers"""
        return self._get(
            "/marketplace/offers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OfferListOffersResponse,
        )

    def redeem_offer(
        self,
        offer_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Redeem Marketplace Reward

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not offer_id:
            raise ValueError(f"Expected a non-empty value for `offer_id` but received {offer_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/marketplace/offers/{offer_id}/redeem",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncOffersResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOffersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncOffersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOffersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncOffersResourceWithStreamingResponse(self)

    async def list_offers(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OfferListOffersResponse:
        """List AI-Targeted Loyalty Offers"""
        return await self._get(
            "/marketplace/offers",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OfferListOffersResponse,
        )

    async def redeem_offer(
        self,
        offer_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Redeem Marketplace Reward

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not offer_id:
            raise ValueError(f"Expected a non-empty value for `offer_id` but received {offer_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/marketplace/offers/{offer_id}/redeem",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class OffersResourceWithRawResponse:
    def __init__(self, offers: OffersResource) -> None:
        self._offers = offers

        self.list_offers = to_raw_response_wrapper(
            offers.list_offers,
        )
        self.redeem_offer = to_raw_response_wrapper(
            offers.redeem_offer,
        )


class AsyncOffersResourceWithRawResponse:
    def __init__(self, offers: AsyncOffersResource) -> None:
        self._offers = offers

        self.list_offers = async_to_raw_response_wrapper(
            offers.list_offers,
        )
        self.redeem_offer = async_to_raw_response_wrapper(
            offers.redeem_offer,
        )


class OffersResourceWithStreamingResponse:
    def __init__(self, offers: OffersResource) -> None:
        self._offers = offers

        self.list_offers = to_streamed_response_wrapper(
            offers.list_offers,
        )
        self.redeem_offer = to_streamed_response_wrapper(
            offers.redeem_offer,
        )


class AsyncOffersResourceWithStreamingResponse:
    def __init__(self, offers: AsyncOffersResource) -> None:
        self._offers = offers

        self.list_offers = async_to_streamed_response_wrapper(
            offers.list_offers,
        )
        self.redeem_offer = async_to_streamed_response_wrapper(
            offers.redeem_offer,
        )
