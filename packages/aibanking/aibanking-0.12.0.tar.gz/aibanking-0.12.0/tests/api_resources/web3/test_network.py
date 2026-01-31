# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.web3 import NetworkGetStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestNetwork:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_status(self, client: Jocall3) -> None:
        network = client.web3.network.get_status()
        assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_status(self, client: Jocall3) -> None:
        response = client.web3.network.with_raw_response.get_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        network = response.parse()
        assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_status(self, client: Jocall3) -> None:
        with client.web3.network.with_streaming_response.get_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            network = response.parse()
            assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncNetwork:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_status(self, async_client: AsyncJocall3) -> None:
        network = await async_client.web3.network.get_status()
        assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.network.with_raw_response.get_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        network = await response.parse()
        assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.network.with_streaming_response.get_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            network = await response.parse()
            assert_matches_type(NetworkGetStatusResponse, network, path=["response"])

        assert cast(Any, response.is_closed) is True
