# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

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
from ...types.investments import (
    portfolio_list_params,
    portfolio_create_params,
    portfolio_update_params,
    portfolio_rebalance_params,
)
from ...types.investments.portfolio_list_response import PortfolioListResponse
from ...types.investments.portfolio_rebalance_response import PortfolioRebalanceResponse

__all__ = ["PortfoliosResource", "AsyncPortfoliosResource"]


class PortfoliosResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PortfoliosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return PortfoliosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PortfoliosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return PortfoliosResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        strategy: Literal["GROWTH", "BALANCED", "INCOME", "ESG_FOCUSED"],
        initial_allocation: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create Strategic Portfolio

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/investments/portfolios",
            body=maybe_transform(
                {
                    "name": name,
                    "strategy": strategy,
                    "initial_allocation": initial_allocation,
                },
                portfolio_create_params.PortfolioCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retrieve(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get Full Portfolio Performance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._get(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update(
        self,
        portfolio_id: str,
        *,
        risk_tolerance: int | Omit = omit,
        strategy: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update Portfolio Strategy

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/investments/portfolios/{portfolio_id}",
            body=maybe_transform(
                {
                    "risk_tolerance": risk_tolerance,
                    "strategy": strategy,
                },
                portfolio_update_params.PortfolioUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PortfolioListResponse:
        """
        List All Investment Portfolios

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/investments/portfolios",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    portfolio_list_params.PortfolioListParams,
                ),
            ),
            cast_to=PortfolioListResponse,
        )

    def rebalance(
        self,
        portfolio_id: str,
        *,
        execution_mode: Literal["AUTO", "CONFIRM_ONLY"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PortfolioRebalanceResponse:
        """
        Trigger Gemini AI Rebalancing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return self._post(
            f"/investments/portfolios/{portfolio_id}/rebalance",
            body=maybe_transform(
                {"execution_mode": execution_mode}, portfolio_rebalance_params.PortfolioRebalanceParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PortfolioRebalanceResponse,
        )


class AsyncPortfoliosResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPortfoliosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncPortfoliosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPortfoliosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncPortfoliosResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        strategy: Literal["GROWTH", "BALANCED", "INCOME", "ESG_FOCUSED"],
        initial_allocation: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create Strategic Portfolio

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/investments/portfolios",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "strategy": strategy,
                    "initial_allocation": initial_allocation,
                },
                portfolio_create_params.PortfolioCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retrieve(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Get Full Portfolio Performance

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._get(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update(
        self,
        portfolio_id: str,
        *,
        risk_tolerance: int | Omit = omit,
        strategy: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update Portfolio Strategy

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/investments/portfolios/{portfolio_id}",
            body=await async_maybe_transform(
                {
                    "risk_tolerance": risk_tolerance,
                    "strategy": strategy,
                },
                portfolio_update_params.PortfolioUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PortfolioListResponse:
        """
        List All Investment Portfolios

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/investments/portfolios",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    portfolio_list_params.PortfolioListParams,
                ),
            ),
            cast_to=PortfolioListResponse,
        )

    async def rebalance(
        self,
        portfolio_id: str,
        *,
        execution_mode: Literal["AUTO", "CONFIRM_ONLY"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PortfolioRebalanceResponse:
        """
        Trigger Gemini AI Rebalancing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return await self._post(
            f"/investments/portfolios/{portfolio_id}/rebalance",
            body=await async_maybe_transform(
                {"execution_mode": execution_mode}, portfolio_rebalance_params.PortfolioRebalanceParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PortfolioRebalanceResponse,
        )


class PortfoliosResourceWithRawResponse:
    def __init__(self, portfolios: PortfoliosResource) -> None:
        self._portfolios = portfolios

        self.create = to_raw_response_wrapper(
            portfolios.create,
        )
        self.retrieve = to_raw_response_wrapper(
            portfolios.retrieve,
        )
        self.update = to_raw_response_wrapper(
            portfolios.update,
        )
        self.list = to_raw_response_wrapper(
            portfolios.list,
        )
        self.rebalance = to_raw_response_wrapper(
            portfolios.rebalance,
        )


class AsyncPortfoliosResourceWithRawResponse:
    def __init__(self, portfolios: AsyncPortfoliosResource) -> None:
        self._portfolios = portfolios

        self.create = async_to_raw_response_wrapper(
            portfolios.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            portfolios.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            portfolios.update,
        )
        self.list = async_to_raw_response_wrapper(
            portfolios.list,
        )
        self.rebalance = async_to_raw_response_wrapper(
            portfolios.rebalance,
        )


class PortfoliosResourceWithStreamingResponse:
    def __init__(self, portfolios: PortfoliosResource) -> None:
        self._portfolios = portfolios

        self.create = to_streamed_response_wrapper(
            portfolios.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            portfolios.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            portfolios.update,
        )
        self.list = to_streamed_response_wrapper(
            portfolios.list,
        )
        self.rebalance = to_streamed_response_wrapper(
            portfolios.rebalance,
        )


class AsyncPortfoliosResourceWithStreamingResponse:
    def __init__(self, portfolios: AsyncPortfoliosResource) -> None:
        self._portfolios = portfolios

        self.create = async_to_streamed_response_wrapper(
            portfolios.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            portfolios.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            portfolios.update,
        )
        self.list = async_to_streamed_response_wrapper(
            portfolios.list,
        )
        self.rebalance = async_to_streamed_response_wrapper(
            portfolios.rebalance,
        )
