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
from ...types.web3 import nft_mint_params
from ..._base_client import make_request_options
from ...types.web3.nft_list_response import NFTListResponse

__all__ = ["NFTsResource", "AsyncNFTsResource"]


class NFTsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> NFTsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return NFTsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> NFTsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return NFTsResourceWithStreamingResponse(self)

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NFTListResponse:
        """List NFT Collection"""
        return self._get(
            "/web3/nfts",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NFTListResponse,
        )

    def mint(
        self,
        *,
        metadata_uri: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Mint Utility NFT

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/web3/nfts/mint",
            body=maybe_transform({"metadata_uri": metadata_uri}, nft_mint_params.NFTMintParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncNFTsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncNFTsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncNFTsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncNFTsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncNFTsResourceWithStreamingResponse(self)

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> NFTListResponse:
        """List NFT Collection"""
        return await self._get(
            "/web3/nfts",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NFTListResponse,
        )

    async def mint(
        self,
        *,
        metadata_uri: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Mint Utility NFT

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/web3/nfts/mint",
            body=await async_maybe_transform({"metadata_uri": metadata_uri}, nft_mint_params.NFTMintParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class NFTsResourceWithRawResponse:
    def __init__(self, nfts: NFTsResource) -> None:
        self._nfts = nfts

        self.list = to_raw_response_wrapper(
            nfts.list,
        )
        self.mint = to_raw_response_wrapper(
            nfts.mint,
        )


class AsyncNFTsResourceWithRawResponse:
    def __init__(self, nfts: AsyncNFTsResource) -> None:
        self._nfts = nfts

        self.list = async_to_raw_response_wrapper(
            nfts.list,
        )
        self.mint = async_to_raw_response_wrapper(
            nfts.mint,
        )


class NFTsResourceWithStreamingResponse:
    def __init__(self, nfts: NFTsResource) -> None:
        self._nfts = nfts

        self.list = to_streamed_response_wrapper(
            nfts.list,
        )
        self.mint = to_streamed_response_wrapper(
            nfts.mint,
        )


class AsyncNFTsResourceWithStreamingResponse:
    def __init__(self, nfts: AsyncNFTsResource) -> None:
        self._nfts = nfts

        self.list = async_to_streamed_response_wrapper(
            nfts.list,
        )
        self.mint = async_to_streamed_response_wrapper(
            nfts.mint,
        )
