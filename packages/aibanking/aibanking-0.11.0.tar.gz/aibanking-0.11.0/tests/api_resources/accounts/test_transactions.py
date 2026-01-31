# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.accounts import (
    TransactionRetrievePendingResponse,
    TransactionRetrieveArchivedResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTransactions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_archived(self, client: Jocall3) -> None:
        transaction = client.accounts.transactions.retrieve_archived(
            account_id="string",
        )
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_archived_with_all_params(self, client: Jocall3) -> None:
        transaction = client.accounts.transactions.retrieve_archived(
            account_id="string",
            year=0,
        )
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_archived(self, client: Jocall3) -> None:
        response = client.accounts.transactions.with_raw_response.retrieve_archived(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_archived(self, client: Jocall3) -> None:
        with client.accounts.transactions.with_streaming_response.retrieve_archived(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_archived(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.transactions.with_raw_response.retrieve_archived(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_pending(self, client: Jocall3) -> None:
        transaction = client.accounts.transactions.retrieve_pending(
            "string",
        )
        assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_pending(self, client: Jocall3) -> None:
        response = client.accounts.transactions.with_raw_response.retrieve_pending(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_pending(self, client: Jocall3) -> None:
        with client.accounts.transactions.with_streaming_response.retrieve_pending(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_pending(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.transactions.with_raw_response.retrieve_pending(
                "",
            )


class TestAsyncTransactions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_archived(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.accounts.transactions.retrieve_archived(
            account_id="string",
        )
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_archived_with_all_params(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.accounts.transactions.retrieve_archived(
            account_id="string",
            year=0,
        )
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_archived(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.transactions.with_raw_response.retrieve_archived(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_archived(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.transactions.with_streaming_response.retrieve_archived(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionRetrieveArchivedResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_archived(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.transactions.with_raw_response.retrieve_archived(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_pending(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.accounts.transactions.retrieve_pending(
            "string",
        )
        assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_pending(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.transactions.with_raw_response.retrieve_pending(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_pending(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.transactions.with_streaming_response.retrieve_pending(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionRetrievePendingResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_pending(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.transactions.with_raw_response.retrieve_pending(
                "",
            )
