# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate.treasury import CashFlowForecastResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCashFlow:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_forecast(self, client: Jocall3) -> None:
        cash_flow = client.corporate.treasury.cash_flow.forecast()
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_forecast_with_all_params(self, client: Jocall3) -> None:
        cash_flow = client.corporate.treasury.cash_flow.forecast(
            horizon_days=0,
        )
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_forecast(self, client: Jocall3) -> None:
        response = client.corporate.treasury.cash_flow.with_raw_response.forecast()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cash_flow = response.parse()
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_forecast(self, client: Jocall3) -> None:
        with client.corporate.treasury.cash_flow.with_streaming_response.forecast() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cash_flow = response.parse()
            assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCashFlow:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_forecast(self, async_client: AsyncJocall3) -> None:
        cash_flow = await async_client.corporate.treasury.cash_flow.forecast()
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_forecast_with_all_params(self, async_client: AsyncJocall3) -> None:
        cash_flow = await async_client.corporate.treasury.cash_flow.forecast(
            horizon_days=0,
        )
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_forecast(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.cash_flow.with_raw_response.forecast()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        cash_flow = await response.parse()
        assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_forecast(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.cash_flow.with_streaming_response.forecast() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            cash_flow = await response.parse()
            assert_matches_type(CashFlowForecastResponse, cash_flow, path=["response"])

        assert cast(Any, response.is_closed) is True
