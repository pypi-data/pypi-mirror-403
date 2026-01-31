# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types import (
    AccountLinkResponse,
    AccountOpenResponse,
    AccountRetrieveMeResponse,
    AccountRetrieveDetailsResponse,
    AccountRetrieveBalanceHistoryResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAccounts:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Jocall3) -> None:
        account = client.accounts.delete(
            "string",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.delete(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.delete(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert account is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_link(self, client: Jocall3) -> None:
        account = client.accounts.link(
            institution_id="string",
            public_token="string",
        )
        assert_matches_type(AccountLinkResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_link(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.link(
            institution_id="string",
            public_token="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountLinkResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_link(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.link(
            institution_id="string",
            public_token="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountLinkResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_open(self, client: Jocall3) -> None:
        account = client.accounts.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        )
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_open_with_all_params(self, client: Jocall3) -> None:
        account = client.accounts.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
            owners=["string", "string"],
        )
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_open(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_open(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountOpenResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_balance_history(self, client: Jocall3) -> None:
        account = client.accounts.retrieve_balance_history(
            account_id="string",
        )
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_balance_history_with_all_params(self, client: Jocall3) -> None:
        account = client.accounts.retrieve_balance_history(
            account_id="string",
            period="1d",
        )
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_balance_history(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.retrieve_balance_history(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_balance_history(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.retrieve_balance_history(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_balance_history(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.with_raw_response.retrieve_balance_history(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_details(self, client: Jocall3) -> None:
        account = client.accounts.retrieve_details(
            "string",
        )
        assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_details(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.retrieve_details(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_details(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.retrieve_details(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_details(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.with_raw_response.retrieve_details(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_me(self, client: Jocall3) -> None:
        account = client.accounts.retrieve_me()
        assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_me(self, client: Jocall3) -> None:
        response = client.accounts.with_raw_response.retrieve_me()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = response.parse()
        assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_me(self, client: Jocall3) -> None:
        with client.accounts.with_streaming_response.retrieve_me() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = response.parse()
            assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAccounts:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.delete(
            "string",
        )
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.delete(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert account is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.delete(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert account is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_link(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.link(
            institution_id="string",
            public_token="string",
        )
        assert_matches_type(AccountLinkResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_link(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.link(
            institution_id="string",
            public_token="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountLinkResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_link(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.link(
            institution_id="string",
            public_token="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountLinkResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_open(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        )
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_open_with_all_params(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
            owners=["string", "string"],
        )
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_open(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountOpenResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_open(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.open(
            currency="USD",
            initial_deposit=8885.832056335083,
            product_type="high_yield_vault",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountOpenResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_balance_history(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.retrieve_balance_history(
            account_id="string",
        )
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_balance_history_with_all_params(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.retrieve_balance_history(
            account_id="string",
            period="1d",
        )
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_balance_history(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.retrieve_balance_history(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_balance_history(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.retrieve_balance_history(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountRetrieveBalanceHistoryResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_balance_history(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.with_raw_response.retrieve_balance_history(
                account_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_details(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.retrieve_details(
            "string",
        )
        assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_details(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.retrieve_details(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_details(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.retrieve_details(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountRetrieveDetailsResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_details(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.with_raw_response.retrieve_details(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_me(self, async_client: AsyncJocall3) -> None:
        account = await async_client.accounts.retrieve_me()
        assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_me(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.with_raw_response.retrieve_me()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        account = await response.parse()
        assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_me(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.with_streaming_response.retrieve_me() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            account = await response.parse()
            assert_matches_type(AccountRetrieveMeResponse, account, path=["response"])

        assert cast(Any, response.is_closed) is True
