# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.accounts import StatementListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStatements:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        statement = client.accounts.statements.list(
            "string",
        )
        assert_matches_type(StatementListResponse, statement, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.accounts.statements.with_raw_response.list(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = response.parse()
        assert_matches_type(StatementListResponse, statement, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.accounts.statements.with_streaming_response.list(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = response.parse()
            assert_matches_type(StatementListResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.statements.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_pdf(self, client: Jocall3) -> None:
        statement = client.accounts.statements.retrieve_pdf(
            statement_id="string",
            account_id="string",
        )
        assert statement is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_pdf(self, client: Jocall3) -> None:
        response = client.accounts.statements.with_raw_response.retrieve_pdf(
            statement_id="string",
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = response.parse()
        assert statement is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_pdf(self, client: Jocall3) -> None:
        with client.accounts.statements.with_streaming_response.retrieve_pdf(
            statement_id="string",
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = response.parse()
            assert statement is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_pdf(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.statements.with_raw_response.retrieve_pdf(
                statement_id="string",
                account_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `statement_id` but received ''"):
            client.accounts.statements.with_raw_response.retrieve_pdf(
                statement_id="",
                account_id="string",
            )


class TestAsyncStatements:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        statement = await async_client.accounts.statements.list(
            "string",
        )
        assert_matches_type(StatementListResponse, statement, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.statements.with_raw_response.list(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = await response.parse()
        assert_matches_type(StatementListResponse, statement, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.statements.with_streaming_response.list(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = await response.parse()
            assert_matches_type(StatementListResponse, statement, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.statements.with_raw_response.list(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_pdf(self, async_client: AsyncJocall3) -> None:
        statement = await async_client.accounts.statements.retrieve_pdf(
            statement_id="string",
            account_id="string",
        )
        assert statement is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_pdf(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.statements.with_raw_response.retrieve_pdf(
            statement_id="string",
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        statement = await response.parse()
        assert statement is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_pdf(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.statements.with_streaming_response.retrieve_pdf(
            statement_id="string",
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            statement = await response.parse()
            assert statement is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_pdf(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.statements.with_raw_response.retrieve_pdf(
                statement_id="string",
                account_id="",
            )

        with pytest.raises(ValueError, match=r"Expected a non-empty value for `statement_id` but received ''"):
            await async_client.accounts.statements.with_raw_response.retrieve_pdf(
                statement_id="",
                account_id="string",
            )
