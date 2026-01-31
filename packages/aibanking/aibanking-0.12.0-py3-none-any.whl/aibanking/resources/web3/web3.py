# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .nfts import (
    NFTsResource,
    AsyncNFTsResource,
    NFTsResourceWithRawResponse,
    AsyncNFTsResourceWithRawResponse,
    NFTsResourceWithStreamingResponse,
    AsyncNFTsResourceWithStreamingResponse,
)
from .network import (
    NetworkResource,
    AsyncNetworkResource,
    NetworkResourceWithRawResponse,
    AsyncNetworkResourceWithRawResponse,
    NetworkResourceWithStreamingResponse,
    AsyncNetworkResourceWithStreamingResponse,
)
from .wallets import (
    WalletsResource,
    AsyncWalletsResource,
    WalletsResourceWithRawResponse,
    AsyncWalletsResourceWithRawResponse,
    WalletsResourceWithStreamingResponse,
    AsyncWalletsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from .contracts import (
    ContractsResource,
    AsyncContractsResource,
    ContractsResourceWithRawResponse,
    AsyncContractsResourceWithRawResponse,
    ContractsResourceWithStreamingResponse,
    AsyncContractsResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from .transactions import (
    TransactionsResource,
    AsyncTransactionsResource,
    TransactionsResourceWithRawResponse,
    AsyncTransactionsResourceWithRawResponse,
    TransactionsResourceWithStreamingResponse,
    AsyncTransactionsResourceWithStreamingResponse,
)

__all__ = ["Web3Resource", "AsyncWeb3Resource"]


class Web3Resource(SyncAPIResource):
    @cached_property
    def network(self) -> NetworkResource:
        return NetworkResource(self._client)

    @cached_property
    def wallets(self) -> WalletsResource:
        return WalletsResource(self._client)

    @cached_property
    def transactions(self) -> TransactionsResource:
        return TransactionsResource(self._client)

    @cached_property
    def nfts(self) -> NFTsResource:
        return NFTsResource(self._client)

    @cached_property
    def contracts(self) -> ContractsResource:
        return ContractsResource(self._client)

    @cached_property
    def with_raw_response(self) -> Web3ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return Web3ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> Web3ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return Web3ResourceWithStreamingResponse(self)


class AsyncWeb3Resource(AsyncAPIResource):
    @cached_property
    def network(self) -> AsyncNetworkResource:
        return AsyncNetworkResource(self._client)

    @cached_property
    def wallets(self) -> AsyncWalletsResource:
        return AsyncWalletsResource(self._client)

    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        return AsyncTransactionsResource(self._client)

    @cached_property
    def nfts(self) -> AsyncNFTsResource:
        return AsyncNFTsResource(self._client)

    @cached_property
    def contracts(self) -> AsyncContractsResource:
        return AsyncContractsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWeb3ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncWeb3ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWeb3ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncWeb3ResourceWithStreamingResponse(self)


class Web3ResourceWithRawResponse:
    def __init__(self, web3: Web3Resource) -> None:
        self._web3 = web3

    @cached_property
    def network(self) -> NetworkResourceWithRawResponse:
        return NetworkResourceWithRawResponse(self._web3.network)

    @cached_property
    def wallets(self) -> WalletsResourceWithRawResponse:
        return WalletsResourceWithRawResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> TransactionsResourceWithRawResponse:
        return TransactionsResourceWithRawResponse(self._web3.transactions)

    @cached_property
    def nfts(self) -> NFTsResourceWithRawResponse:
        return NFTsResourceWithRawResponse(self._web3.nfts)

    @cached_property
    def contracts(self) -> ContractsResourceWithRawResponse:
        return ContractsResourceWithRawResponse(self._web3.contracts)


class AsyncWeb3ResourceWithRawResponse:
    def __init__(self, web3: AsyncWeb3Resource) -> None:
        self._web3 = web3

    @cached_property
    def network(self) -> AsyncNetworkResourceWithRawResponse:
        return AsyncNetworkResourceWithRawResponse(self._web3.network)

    @cached_property
    def wallets(self) -> AsyncWalletsResourceWithRawResponse:
        return AsyncWalletsResourceWithRawResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithRawResponse:
        return AsyncTransactionsResourceWithRawResponse(self._web3.transactions)

    @cached_property
    def nfts(self) -> AsyncNFTsResourceWithRawResponse:
        return AsyncNFTsResourceWithRawResponse(self._web3.nfts)

    @cached_property
    def contracts(self) -> AsyncContractsResourceWithRawResponse:
        return AsyncContractsResourceWithRawResponse(self._web3.contracts)


class Web3ResourceWithStreamingResponse:
    def __init__(self, web3: Web3Resource) -> None:
        self._web3 = web3

    @cached_property
    def network(self) -> NetworkResourceWithStreamingResponse:
        return NetworkResourceWithStreamingResponse(self._web3.network)

    @cached_property
    def wallets(self) -> WalletsResourceWithStreamingResponse:
        return WalletsResourceWithStreamingResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> TransactionsResourceWithStreamingResponse:
        return TransactionsResourceWithStreamingResponse(self._web3.transactions)

    @cached_property
    def nfts(self) -> NFTsResourceWithStreamingResponse:
        return NFTsResourceWithStreamingResponse(self._web3.nfts)

    @cached_property
    def contracts(self) -> ContractsResourceWithStreamingResponse:
        return ContractsResourceWithStreamingResponse(self._web3.contracts)


class AsyncWeb3ResourceWithStreamingResponse:
    def __init__(self, web3: AsyncWeb3Resource) -> None:
        self._web3 = web3

    @cached_property
    def network(self) -> AsyncNetworkResourceWithStreamingResponse:
        return AsyncNetworkResourceWithStreamingResponse(self._web3.network)

    @cached_property
    def wallets(self) -> AsyncWalletsResourceWithStreamingResponse:
        return AsyncWalletsResourceWithStreamingResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithStreamingResponse:
        return AsyncTransactionsResourceWithStreamingResponse(self._web3.transactions)

    @cached_property
    def nfts(self) -> AsyncNFTsResourceWithStreamingResponse:
        return AsyncNFTsResourceWithStreamingResponse(self._web3.nfts)

    @cached_property
    def contracts(self) -> AsyncContractsResourceWithStreamingResponse:
        return AsyncContractsResourceWithStreamingResponse(self._web3.contracts)
