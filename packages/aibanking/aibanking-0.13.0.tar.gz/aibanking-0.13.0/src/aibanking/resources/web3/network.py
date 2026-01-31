# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.web3.network_get_status_response import NetworkGetStatusResponse

__all__ = ["NetworkResource", "AsyncNetworkResource"]


class NetworkResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NetworkResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return NetworkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NetworkResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return NetworkResourceWithStreamingResponse(self)

    def get_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NetworkGetStatusResponse:
        """Get Blockchain Network Health"""
        return self._get(
            "/web3/network/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NetworkGetStatusResponse,
        )


class AsyncNetworkResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNetworkResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncNetworkResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNetworkResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncNetworkResourceWithStreamingResponse(self)

    async def get_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NetworkGetStatusResponse:
        """Get Blockchain Network Health"""
        return await self._get(
            "/web3/network/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NetworkGetStatusResponse,
        )


class NetworkResourceWithRawResponse:
    def __init__(self, network: NetworkResource) -> None:
        self._network = network

        self.get_status = to_raw_response_wrapper(
            network.get_status,
        )


class AsyncNetworkResourceWithRawResponse:
    def __init__(self, network: AsyncNetworkResource) -> None:
        self._network = network

        self.get_status = async_to_raw_response_wrapper(
            network.get_status,
        )


class NetworkResourceWithStreamingResponse:
    def __init__(self, network: NetworkResource) -> None:
        self._network = network

        self.get_status = to_streamed_response_wrapper(
            network.get_status,
        )


class AsyncNetworkResourceWithStreamingResponse:
    def __init__(self, network: AsyncNetworkResource) -> None:
        self._network = network

        self.get_status = async_to_streamed_response_wrapper(
            network.get_status,
        )
