# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSweeping:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_configure_rules(self, client: Jocall3) -> None:
        sweeping = client.corporate.treasury.sweeping.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_configure_rules_with_all_params(self, client: Jocall3) -> None:
        sweeping = client.corporate.treasury.sweeping.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
            frequency="weekly",
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_configure_rules(self, client: Jocall3) -> None:
        response = client.corporate.treasury.sweeping.with_raw_response.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sweeping = response.parse()
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_configure_rules(self, client: Jocall3) -> None:
        with client.corporate.treasury.sweeping.with_streaming_response.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sweeping = response.parse()
            assert sweeping is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_sweep(self, client: Jocall3) -> None:
        sweeping = client.corporate.treasury.sweeping.execute_sweep(
            rule_id="string",
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_sweep(self, client: Jocall3) -> None:
        response = client.corporate.treasury.sweeping.with_raw_response.execute_sweep(
            rule_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sweeping = response.parse()
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_sweep(self, client: Jocall3) -> None:
        with client.corporate.treasury.sweeping.with_streaming_response.execute_sweep(
            rule_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sweeping = response.parse()
            assert sweeping is None

        assert cast(Any, response.is_closed) is True


class TestAsyncSweeping:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_configure_rules(self, async_client: AsyncJocall3) -> None:
        sweeping = await async_client.corporate.treasury.sweeping.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_configure_rules_with_all_params(self, async_client: AsyncJocall3) -> None:
        sweeping = await async_client.corporate.treasury.sweeping.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
            frequency="weekly",
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_configure_rules(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.sweeping.with_raw_response.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sweeping = await response.parse()
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_configure_rules(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.sweeping.with_streaming_response.configure_rules(
            source_account="string",
            target_account="string",
            threshold=151.0206397332503,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sweeping = await response.parse()
            assert sweeping is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_sweep(self, async_client: AsyncJocall3) -> None:
        sweeping = await async_client.corporate.treasury.sweeping.execute_sweep(
            rule_id="string",
        )
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_sweep(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.treasury.sweeping.with_raw_response.execute_sweep(
            rule_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sweeping = await response.parse()
        assert sweeping is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_sweep(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.treasury.sweeping.with_streaming_response.execute_sweep(
            rule_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sweeping = await response.parse()
            assert sweeping is None

        assert cast(Any, response.is_closed) is True
