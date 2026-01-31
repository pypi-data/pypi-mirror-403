# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.transactions import InsightGetSpendingTrendsResponse, InsightGetCashFlowPredictionResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestInsights:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_cash_flow_prediction(self, client: Jocall3) -> None:
        insight = client.transactions.insights.get_cash_flow_prediction()
        assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_cash_flow_prediction(self, client: Jocall3) -> None:
        response = client.transactions.insights.with_raw_response.get_cash_flow_prediction()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        insight = response.parse()
        assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_cash_flow_prediction(self, client: Jocall3) -> None:
        with client.transactions.insights.with_streaming_response.get_cash_flow_prediction() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            insight = response.parse()
            assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_spending_trends(self, client: Jocall3) -> None:
        insight = client.transactions.insights.get_spending_trends()
        assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_spending_trends(self, client: Jocall3) -> None:
        response = client.transactions.insights.with_raw_response.get_spending_trends()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        insight = response.parse()
        assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_spending_trends(self, client: Jocall3) -> None:
        with client.transactions.insights.with_streaming_response.get_spending_trends() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            insight = response.parse()
            assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncInsights:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_cash_flow_prediction(self, async_client: AsyncJocall3) -> None:
        insight = await async_client.transactions.insights.get_cash_flow_prediction()
        assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_cash_flow_prediction(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.insights.with_raw_response.get_cash_flow_prediction()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        insight = await response.parse()
        assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_cash_flow_prediction(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.insights.with_streaming_response.get_cash_flow_prediction() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            insight = await response.parse()
            assert_matches_type(InsightGetCashFlowPredictionResponse, insight, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_spending_trends(self, async_client: AsyncJocall3) -> None:
        insight = await async_client.transactions.insights.get_spending_trends()
        assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_spending_trends(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.insights.with_raw_response.get_spending_trends()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        insight = await response.parse()
        assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_spending_trends(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.insights.with_streaming_response.get_spending_trends() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            insight = await response.parse()
            assert_matches_type(InsightGetSpendingTrendsResponse, insight, path=["response"])

        assert cast(Any, response.is_closed) is True
