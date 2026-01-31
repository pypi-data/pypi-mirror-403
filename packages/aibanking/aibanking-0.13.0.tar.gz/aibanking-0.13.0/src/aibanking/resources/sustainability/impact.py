# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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
from ...types.sustainability import impact_list_global_green_projects_params
from ...types.sustainability.impact_retrieve_portfolio_impact_response import ImpactRetrievePortfolioImpactResponse
from ...types.sustainability.impact_list_global_green_projects_response import ImpactListGlobalGreenProjectsResponse

__all__ = ["ImpactResource", "AsyncImpactResource"]


class ImpactResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ImpactResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return ImpactResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ImpactResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return ImpactResourceWithStreamingResponse(self)

    def list_global_green_projects(
        self,
        *,
        continent: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ImpactListGlobalGreenProjectsResponse:
        """
        Search Global Green Projects

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/sustainability/impact/projects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"continent": continent},
                    impact_list_global_green_projects_params.ImpactListGlobalGreenProjectsParams,
                ),
            ),
            cast_to=ImpactListGlobalGreenProjectsResponse,
        )

    def retrieve_portfolio_impact(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ImpactRetrievePortfolioImpactResponse:
        """ESG Portfolio Impact Analysis"""
        return self._get(
            "/sustainability/impact/portfolio",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ImpactRetrievePortfolioImpactResponse,
        )


class AsyncImpactResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncImpactResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncImpactResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncImpactResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncImpactResourceWithStreamingResponse(self)

    async def list_global_green_projects(
        self,
        *,
        continent: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ImpactListGlobalGreenProjectsResponse:
        """
        Search Global Green Projects

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/sustainability/impact/projects",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"continent": continent},
                    impact_list_global_green_projects_params.ImpactListGlobalGreenProjectsParams,
                ),
            ),
            cast_to=ImpactListGlobalGreenProjectsResponse,
        )

    async def retrieve_portfolio_impact(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ImpactRetrievePortfolioImpactResponse:
        """ESG Portfolio Impact Analysis"""
        return await self._get(
            "/sustainability/impact/portfolio",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ImpactRetrievePortfolioImpactResponse,
        )


class ImpactResourceWithRawResponse:
    def __init__(self, impact: ImpactResource) -> None:
        self._impact = impact

        self.list_global_green_projects = to_raw_response_wrapper(
            impact.list_global_green_projects,
        )
        self.retrieve_portfolio_impact = to_raw_response_wrapper(
            impact.retrieve_portfolio_impact,
        )


class AsyncImpactResourceWithRawResponse:
    def __init__(self, impact: AsyncImpactResource) -> None:
        self._impact = impact

        self.list_global_green_projects = async_to_raw_response_wrapper(
            impact.list_global_green_projects,
        )
        self.retrieve_portfolio_impact = async_to_raw_response_wrapper(
            impact.retrieve_portfolio_impact,
        )


class ImpactResourceWithStreamingResponse:
    def __init__(self, impact: ImpactResource) -> None:
        self._impact = impact

        self.list_global_green_projects = to_streamed_response_wrapper(
            impact.list_global_green_projects,
        )
        self.retrieve_portfolio_impact = to_streamed_response_wrapper(
            impact.retrieve_portfolio_impact,
        )


class AsyncImpactResourceWithStreamingResponse:
    def __init__(self, impact: AsyncImpactResource) -> None:
        self._impact = impact

        self.list_global_green_projects = async_to_streamed_response_wrapper(
            impact.list_global_green_projects,
        )
        self.retrieve_portfolio_impact = async_to_streamed_response_wrapper(
            impact.retrieve_portfolio_impact,
        )
