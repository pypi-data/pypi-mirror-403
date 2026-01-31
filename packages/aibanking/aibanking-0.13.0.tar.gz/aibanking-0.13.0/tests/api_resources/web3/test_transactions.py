# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.web3 import (
    TransactionSendResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTransactions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_bridge(self, client: Jocall3) -> None:
        transaction = client.web3.transactions.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_bridge(self, client: Jocall3) -> None:
        response = client.web3.transactions.with_raw_response.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_bridge(self, client: Jocall3) -> None:
        with client.web3.transactions.with_streaming_response.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_initiate(self, client: Jocall3) -> None:
        transaction = client.web3.transactions.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_initiate(self, client: Jocall3) -> None:
        response = client.web3.transactions.with_raw_response.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_initiate(self, client: Jocall3) -> None:
        with client.web3.transactions.with_streaming_response.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send(self, client: Jocall3) -> None:
        transaction = client.web3.transactions.send(
            token="string",
            amount="string",
            to="string",
        )
        assert_matches_type(TransactionSendResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_send(self, client: Jocall3) -> None:
        response = client.web3.transactions.with_raw_response.send(
            token="string",
            amount="string",
            to="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionSendResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_send(self, client: Jocall3) -> None:
        with client.web3.transactions.with_streaming_response.send(
            token="string",
            amount="string",
            to="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionSendResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_swap(self, client: Jocall3) -> None:
        transaction = client.web3.transactions.swap(
            amount="string",
            from_token="string",
            to_token="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_swap(self, client: Jocall3) -> None:
        response = client.web3.transactions.with_raw_response.swap(
            amount="string",
            from_token="string",
            to_token="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_swap(self, client: Jocall3) -> None:
        with client.web3.transactions.with_streaming_response.swap(
            amount="string",
            from_token="string",
            to_token="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True


class TestAsyncTransactions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_bridge(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.web3.transactions.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_bridge(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.transactions.with_raw_response.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_bridge(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.transactions.with_streaming_response.bridge(
            token="string",
            amount="string",
            dest_chain="string",
            source_chain="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_initiate(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.web3.transactions.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_initiate(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.transactions.with_raw_response.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_initiate(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.transactions.with_streaming_response.initiate(
            amount=8684.340121544215,
            asset="string",
            wallet_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.web3.transactions.send(
            token="string",
            amount="string",
            to="string",
        )
        assert_matches_type(TransactionSendResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_send(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.transactions.with_raw_response.send(
            token="string",
            amount="string",
            to="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionSendResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_send(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.transactions.with_streaming_response.send(
            token="string",
            amount="string",
            to="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionSendResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_swap(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.web3.transactions.swap(
            amount="string",
            from_token="string",
            to_token="string",
        )
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_swap(self, async_client: AsyncJocall3) -> None:
        response = await async_client.web3.transactions.with_raw_response.swap(
            amount="string",
            from_token="string",
            to_token="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert transaction is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_swap(self, async_client: AsyncJocall3) -> None:
        async with async_client.web3.transactions.with_streaming_response.swap(
            amount="string",
            from_token="string",
            to_token="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert transaction is None

        assert cast(Any, response.is_closed) is True
