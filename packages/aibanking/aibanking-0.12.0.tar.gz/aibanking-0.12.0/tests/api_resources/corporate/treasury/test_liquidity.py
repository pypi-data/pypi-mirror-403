# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate.treasury import (
    LiquidityOptimizeResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLiquidity:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_configure_pooling(self, client: Jocall3) -> None:
        liquidity = client.corporate.treasury.liquidity.configure_pooling()
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_configure_pooling_with_all_params(self, client: Jocall3) -> None:
        liquidity = client.corporate.treasury.liquidity.configure_pooling(
            source_account_ids=["string", "string"],
            target_account_id="string",
        )
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_configure_pooling(self, client: Jocall3) -> None:
        response = client.corporate.treasury.liquidity.with_raw_response.configure_pooling()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        liquidity = response.parse()
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_configure_pooling(self, client: Jocall3) -> None:
        with client.corporate.treasury.liquidity.with_streaming_response.configure_pooling() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            liquidity = response.parse()
            assert liquidity is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_optimize(self, client: Jocall3) -> None:
        liquidity = client.corporate.treasury.liquidity.optimize()
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_optimize_with_all_params(self, client: Jocall3) -> None:
        liquidity = client.corporate.treasury.liquidity.optimize(
            sweep_excess=True,
            target_reserve=3283.3648412254447,
        )
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_optimize(self, client: Jocall3) -> None:
        response = client.corporate.treasury.liquidity.with_raw_response.optimize()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        liquidity = response.parse()
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_optimize(self, client: Jocall3) -> None:
        with client.corporate.treasury.liquidity.with_streaming_response.optimize() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            liquidity = response.parse()
            assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncLiquidity:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_configure_pooling(self, async_client: AsyncJocall3) -> None:
        liquidity = await async_client.corporate.treasury.liquidity.configure_pooling()
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_configure_pooling_with_all_params(self, async_client: AsyncJocall3) -> None:
        liquidity = await async_client.corporate.treasury.liquidity.configure_pooling(
            source_account_ids=["string", "string"],
            target_account_id="string",
        )
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_configure_pooling(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.liquidity.with_raw_response.configure_pooling()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        liquidity = await response.parse()
        assert liquidity is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_configure_pooling(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.liquidity.with_streaming_response.configure_pooling() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            liquidity = await response.parse()
            assert liquidity is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_optimize(self, async_client: AsyncJocall3) -> None:
        liquidity = await async_client.corporate.treasury.liquidity.optimize()
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_optimize_with_all_params(self, async_client: AsyncJocall3) -> None:
        liquidity = await async_client.corporate.treasury.liquidity.optimize(
            sweep_excess=True,
            target_reserve=3283.3648412254447,
        )
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_optimize(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.liquidity.with_raw_response.optimize()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        liquidity = await response.parse()
        assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_optimize(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.liquidity.with_streaming_response.optimize() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            liquidity = await response.parse()
            assert_matches_type(LiquidityOptimizeResponse, liquidity, path=["response"])

        assert cast(Any, response.is_closed) is True
