# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.web3 import NFTListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestNFTs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        nft = client.web3.nfts.list()
        assert_matches_type(NFTListResponse, nft, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.web3.nfts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        nft = response.parse()
        assert_matches_type(NFTListResponse, nft, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.web3.nfts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            nft = response.parse()
            assert_matches_type(NFTListResponse, nft, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_mint(self, client: Jocall3) -> None:
        nft = client.web3.nfts.mint(
            metadata_uri="string",
        )
        assert nft is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_mint(self, client: Jocall3) -> None:
        response = client.web3.nfts.with_raw_response.mint(
            metadata_uri="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        nft = response.parse()
        assert nft is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_mint(self, client: Jocall3) -> None:
        with client.web3.nfts.with_streaming_response.mint(
            metadata_uri="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            nft = response.parse()
            assert nft is None

        assert cast(Any, response.is_closed) is True


class TestAsyncNFTs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        nft = await async_client.web3.nfts.list()
        assert_matches_type(NFTListResponse, nft, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.nfts.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        nft = await response.parse()
        assert_matches_type(NFTListResponse, nft, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.nfts.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            nft = await response.parse()
            assert_matches_type(NFTListResponse, nft, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_mint(self, async_client: AsyncJocall3) -> None:
        nft = await async_client.web3.nfts.mint(
            metadata_uri="string",
        )
        assert nft is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_mint(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.nfts.with_raw_response.mint(
            metadata_uri="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        nft = await response.parse()
        assert nft is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_mint(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.nfts.with_streaming_response.mint(
            metadata_uri="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            nft = await response.parse()
            assert nft is None

        assert cast(Any, response.is_closed) is True
