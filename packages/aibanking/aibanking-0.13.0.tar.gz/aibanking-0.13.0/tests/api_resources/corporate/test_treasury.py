# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate import TreasuryGetLiquidityPositionsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTreasury:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_bulk_payouts(self, client: Jocall3) -> None:
        treasury = client.corporate.treasury.execute_bulk_payouts(
            payouts=[{}, {}],
        )
        assert treasury is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_bulk_payouts(self, client: Jocall3) -> None:
        response = client.corporate.treasury.with_raw_response.execute_bulk_payouts(
            payouts=[{}, {}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        treasury = response.parse()
        assert treasury is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_bulk_payouts(self, client: Jocall3) -> None:
        with client.corporate.treasury.with_streaming_response.execute_bulk_payouts(
            payouts=[{}, {}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            treasury = response.parse()
            assert treasury is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_liquidity_positions(self, client: Jocall3) -> None:
        treasury = client.corporate.treasury.get_liquidity_positions()
        assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_liquidity_positions(self, client: Jocall3) -> None:
        response = client.corporate.treasury.with_raw_response.get_liquidity_positions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        treasury = response.parse()
        assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_liquidity_positions(self, client: Jocall3) -> None:
        with client.corporate.treasury.with_streaming_response.get_liquidity_positions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            treasury = response.parse()
            assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncTreasury:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_bulk_payouts(self, async_client: AsyncJocall3) -> None:
        treasury = await async_client.corporate.treasury.execute_bulk_payouts(
            payouts=[{}, {}],
        )
        assert treasury is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_bulk_payouts(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.with_raw_response.execute_bulk_payouts(
            payouts=[{}, {}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        treasury = await response.parse()
        assert treasury is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_bulk_payouts(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.with_streaming_response.execute_bulk_payouts(
            payouts=[{}, {}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            treasury = await response.parse()
            assert treasury is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_liquidity_positions(self, async_client: AsyncJocall3) -> None:
        treasury = await async_client.corporate.treasury.get_liquidity_positions()
        assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_liquidity_positions(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.with_raw_response.get_liquidity_positions()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        treasury = await response.parse()
        assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_liquidity_positions(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.with_streaming_response.get_liquidity_positions() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            treasury = await response.parse()
            assert_matches_type(TreasuryGetLiquidityPositionsResponse, treasury, path=["response"])

        assert cast(Any, response.is_closed) is True
