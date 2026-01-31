# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .offers import (
    OffersResource,
    AsyncOffersResource,
    OffersResourceWithRawResponse,
    AsyncOffersResourceWithRawResponse,
    OffersResourceWithStreamingResponse,
    AsyncOffersResourceWithStreamingResponse,
)
from ...types import marketplace_list_products_params
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

__all__ = ["MarketplaceResource", "AsyncMarketplaceResource"]


class MarketplaceResource(SyncAPIResource):
    @cached_property
    def offers(self) -> OffersResource:
        return OffersResource(self._client)

    @cached_property
    def with_raw_response(self) -> MarketplaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return MarketplaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MarketplaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return MarketplaceResourceWithStreamingResponse(self)

    def list_products(
        self,
        *,
        ai_personalization_level: str | Omit = omit,
        category: str | Omit = omit,
        limit: int | Omit = omit,
        min_rating: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a personalized, AI-curated list of products and services from the
        Plato AI marketplace, tailored to the user's financial profile, goals, and
        spending patterns. Includes options for filtering and advanced search.

        Args:
          ai_personalization_level: Filter by AI personalization level (e.g., low, medium, high). 'High' means
              highly relevant to user's specific needs.

          category: Filter products by category (e.g., loans, insurance, credit_cards, investments).

          limit: Maximum number of items to return in a single page.

          min_rating: Minimum user rating for products (0-5).

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/marketplace/products",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "ai_personalization_level": ai_personalization_level,
                        "category": category,
                        "limit": limit,
                        "min_rating": min_rating,
                        "offset": offset,
                    },
                    marketplace_list_products_params.MarketplaceListProductsParams,
                ),
            ),
            cast_to=object,
        )


class AsyncMarketplaceResource(AsyncAPIResource):
    @cached_property
    def offers(self) -> AsyncOffersResource:
        return AsyncOffersResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncMarketplaceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncMarketplaceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMarketplaceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncMarketplaceResourceWithStreamingResponse(self)

    async def list_products(
        self,
        *,
        ai_personalization_level: str | Omit = omit,
        category: str | Omit = omit,
        limit: int | Omit = omit,
        min_rating: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a personalized, AI-curated list of products and services from the
        Plato AI marketplace, tailored to the user's financial profile, goals, and
        spending patterns. Includes options for filtering and advanced search.

        Args:
          ai_personalization_level: Filter by AI personalization level (e.g., low, medium, high). 'High' means
              highly relevant to user's specific needs.

          category: Filter products by category (e.g., loans, insurance, credit_cards, investments).

          limit: Maximum number of items to return in a single page.

          min_rating: Minimum user rating for products (0-5).

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/marketplace/products",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "ai_personalization_level": ai_personalization_level,
                        "category": category,
                        "limit": limit,
                        "min_rating": min_rating,
                        "offset": offset,
                    },
                    marketplace_list_products_params.MarketplaceListProductsParams,
                ),
            ),
            cast_to=object,
        )


class MarketplaceResourceWithRawResponse:
    def __init__(self, marketplace: MarketplaceResource) -> None:
        self._marketplace = marketplace

        self.list_products = to_raw_response_wrapper(
            marketplace.list_products,
        )

    @cached_property
    def offers(self) -> OffersResourceWithRawResponse:
        return OffersResourceWithRawResponse(self._marketplace.offers)


class AsyncMarketplaceResourceWithRawResponse:
    def __init__(self, marketplace: AsyncMarketplaceResource) -> None:
        self._marketplace = marketplace

        self.list_products = async_to_raw_response_wrapper(
            marketplace.list_products,
        )

    @cached_property
    def offers(self) -> AsyncOffersResourceWithRawResponse:
        return AsyncOffersResourceWithRawResponse(self._marketplace.offers)


class MarketplaceResourceWithStreamingResponse:
    def __init__(self, marketplace: MarketplaceResource) -> None:
        self._marketplace = marketplace

        self.list_products = to_streamed_response_wrapper(
            marketplace.list_products,
        )

    @cached_property
    def offers(self) -> OffersResourceWithStreamingResponse:
        return OffersResourceWithStreamingResponse(self._marketplace.offers)


class AsyncMarketplaceResourceWithStreamingResponse:
    def __init__(self, marketplace: AsyncMarketplaceResource) -> None:
        self._marketplace = marketplace

        self.list_products = async_to_streamed_response_wrapper(
            marketplace.list_products,
        )

    @cached_property
    def offers(self) -> AsyncOffersResourceWithStreamingResponse:
        return AsyncOffersResourceWithStreamingResponse(self._marketplace.offers)
