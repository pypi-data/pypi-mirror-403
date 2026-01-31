# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.investments import (
    PortfolioListResponse,
    PortfolioRebalanceResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPortfolios:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.create(
            name="string",
            strategy="GROWTH",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.create(
            name="string",
            strategy="GROWTH",
            initial_allocation={},
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Jocall3) -> None:
        response = client.investments.portfolios.with_raw_response.create(
            name="string",
            strategy="GROWTH",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Jocall3) -> None:
        with client.investments.portfolios.with_streaming_response.create(
            name="string",
            strategy="GROWTH",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.retrieve(
            "string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Jocall3) -> None:
        response = client.investments.portfolios.with_raw_response.retrieve(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Jocall3) -> None:
        with client.investments.portfolios.with_streaming_response.retrieve(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            client.investments.portfolios.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.update(
            portfolio_id="string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.update(
            portfolio_id="string",
            risk_tolerance=9686,
            strategy="string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Jocall3) -> None:
        response = client.investments.portfolios.with_raw_response.update(
            portfolio_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Jocall3) -> None:
        with client.investments.portfolios.with_streaming_response.update(
            portfolio_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            client.investments.portfolios.with_raw_response.update(
                portfolio_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.list()
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.list(
            limit=0,
            offset=0,
        )
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.investments.portfolios.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = response.parse()
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.investments.portfolios.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = response.parse()
            assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_rebalance(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.rebalance(
            portfolio_id="string",
        )
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_rebalance_with_all_params(self, client: Jocall3) -> None:
        portfolio = client.investments.portfolios.rebalance(
            portfolio_id="string",
            execution_mode="CONFIRM_ONLY",
        )
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_rebalance(self, client: Jocall3) -> None:
        response = client.investments.portfolios.with_raw_response.rebalance(
            portfolio_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = response.parse()
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_rebalance(self, client: Jocall3) -> None:
        with client.investments.portfolios.with_streaming_response.rebalance(
            portfolio_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = response.parse()
            assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_rebalance(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            client.investments.portfolios.with_raw_response.rebalance(
                portfolio_id="",
            )


class TestAsyncPortfolios:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.create(
            name="string",
            strategy="GROWTH",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.create(
            name="string",
            strategy="GROWTH",
            initial_allocation={},
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncJocall3) -> None:
        response = await async_client.investments.portfolios.with_raw_response.create(
            name="string",
            strategy="GROWTH",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = await response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncJocall3) -> None:
        async with async_client.investments.portfolios.with_streaming_response.create(
            name="string",
            strategy="GROWTH",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = await response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.retrieve(
            "string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncJocall3) -> None:
        response = await async_client.investments.portfolios.with_raw_response.retrieve(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = await response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncJocall3) -> None:
        async with async_client.investments.portfolios.with_streaming_response.retrieve(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = await response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            await async_client.investments.portfolios.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.update(
            portfolio_id="string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.update(
            portfolio_id="string",
            risk_tolerance=9686,
            strategy="string",
        )
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncJocall3) -> None:
        response = await async_client.investments.portfolios.with_raw_response.update(
            portfolio_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = await response.parse()
        assert portfolio is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncJocall3) -> None:
        async with async_client.investments.portfolios.with_streaming_response.update(
            portfolio_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = await response.parse()
            assert portfolio is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            await async_client.investments.portfolios.with_raw_response.update(
                portfolio_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.list()
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.list(
            limit=0,
            offset=0,
        )
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.investments.portfolios.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = await response.parse()
        assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.investments.portfolios.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = await response.parse()
            assert_matches_type(PortfolioListResponse, portfolio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_rebalance(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.rebalance(
            portfolio_id="string",
        )
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_rebalance_with_all_params(self, async_client: AsyncJocall3) -> None:
        portfolio = await async_client.investments.portfolios.rebalance(
            portfolio_id="string",
            execution_mode="CONFIRM_ONLY",
        )
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_rebalance(self, async_client: AsyncJocall3) -> None:
        response = await async_client.investments.portfolios.with_raw_response.rebalance(
            portfolio_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        portfolio = await response.parse()
        assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_rebalance(self, async_client: AsyncJocall3) -> None:
        async with async_client.investments.portfolios.with_streaming_response.rebalance(
            portfolio_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            portfolio = await response.parse()
            assert_matches_type(PortfolioRebalanceResponse, portfolio, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_rebalance(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `portfolio_id` but received ''"):
            await async_client.investments.portfolios.with_raw_response.rebalance(
                portfolio_id="",
            )
