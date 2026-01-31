# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestContracts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_deploy(self, client: Jocall3) -> None:
        contract = client.web3.contracts.deploy(
            abi={},
            bytecode="string",
        )
        assert contract is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_deploy(self, client: Jocall3) -> None:
        response = client.web3.contracts.with_raw_response.deploy(
            abi={},
            bytecode="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        contract = response.parse()
        assert contract is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_deploy(self, client: Jocall3) -> None:
        with client.web3.contracts.with_streaming_response.deploy(
            abi={},
            bytecode="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            contract = response.parse()
            assert contract is None

        assert cast(Any, response.is_closed) is True


class TestAsyncContracts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_deploy(self, async_client: AsyncJocall3) -> None:
        contract = await async_client.web3.contracts.deploy(
            abi={},
            bytecode="string",
        )
        assert contract is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_deploy(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.contracts.with_raw_response.deploy(
            abi={},
            bytecode="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        contract = await response.parse()
        assert contract is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_deploy(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.contracts.with_streaming_response.deploy(
            abi={},
            bytecode="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            contract = await response.parse()
            assert contract is None

        assert cast(Any, response.is_closed) is True
