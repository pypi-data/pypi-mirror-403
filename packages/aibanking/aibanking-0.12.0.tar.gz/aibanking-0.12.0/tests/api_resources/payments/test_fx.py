# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking._utils import parse_date
from aibanking.types.payments import (
    FxGetRatesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFx:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_book_deal(self, client: Jocall3) -> None:
        fx = client.payments.fx.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        )
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_book_deal(self, client: Jocall3) -> None:
        response = client.payments.fx.with_raw_response.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = response.parse()
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_book_deal(self, client: Jocall3) -> None:
        with client.payments.fx.with_streaming_response.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = response.parse()
            assert fx is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_conversion(self, client: Jocall3) -> None:
        fx = client.payments.fx.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        )
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_conversion(self, client: Jocall3) -> None:
        response = client.payments.fx.with_raw_response.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = response.parse()
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_conversion(self, client: Jocall3) -> None:
        with client.payments.fx.with_streaming_response.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = response.parse()
            assert fx is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_rates(self, client: Jocall3) -> None:
        fx = client.payments.fx.get_rates(
            pair="EURUSD",
        )
        assert_matches_type(FxGetRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_rates(self, client: Jocall3) -> None:
        response = client.payments.fx.with_raw_response.get_rates(
            pair="EURUSD",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = response.parse()
        assert_matches_type(FxGetRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_rates(self, client: Jocall3) -> None:
        with client.payments.fx.with_streaming_response.get_rates(
            pair="EURUSD",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = response.parse()
            assert_matches_type(FxGetRatesResponse, fx, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncFx:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_book_deal(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        )
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_book_deal(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.fx.with_raw_response.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = await response.parse()
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_book_deal(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.fx.with_streaming_response.book_deal(
            amount=9860.991425096323,
            pair="string",
            value_date=parse_date("1972-06-20"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = await response.parse()
            assert fx is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_conversion(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        )
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_conversion(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.fx.with_raw_response.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = await response.parse()
        assert fx is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_conversion(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.fx.with_streaming_response.execute_conversion(
            amount=7305.266093092808,
            from_="string",
            to="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = await response.parse()
            assert fx is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_rates(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.get_rates(
            pair="EURUSD",
        )
        assert_matches_type(FxGetRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_rates(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.fx.with_raw_response.get_rates(
            pair="EURUSD",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = await response.parse()
        assert_matches_type(FxGetRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_rates(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.fx.with_streaming_response.get_rates(
            pair="EURUSD",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = await response.parse()
            assert_matches_type(FxGetRatesResponse, fx, path=["response"])

        assert cast(Any, response.is_closed) is True
