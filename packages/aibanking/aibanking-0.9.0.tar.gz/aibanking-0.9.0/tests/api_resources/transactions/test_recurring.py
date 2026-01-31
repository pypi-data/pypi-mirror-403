# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.transactions import RecurringListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRecurring:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Jocall3) -> None:
        recurring = client.transactions.recurring.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        )
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Jocall3) -> None:
        response = client.transactions.recurring.with_raw_response.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = response.parse()
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Jocall3) -> None:
        with client.transactions.recurring.with_streaming_response.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = response.parse()
            assert recurring is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        recurring = client.transactions.recurring.list()
        assert_matches_type(RecurringListResponse, recurring, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.transactions.recurring.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = response.parse()
        assert_matches_type(RecurringListResponse, recurring, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.transactions.recurring.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = response.parse()
            assert_matches_type(RecurringListResponse, recurring, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cancel(self, client: Jocall3) -> None:
        recurring = client.transactions.recurring.cancel(
            "string",
        )
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cancel(self, client: Jocall3) -> None:
        response = client.transactions.recurring.with_raw_response.cancel(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = response.parse()
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cancel(self, client: Jocall3) -> None:
        with client.transactions.recurring.with_streaming_response.cancel(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = response.parse()
            assert recurring is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cancel(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `recurring_id` but received ''"):
            client.transactions.recurring.with_raw_response.cancel(
                "",
            )


class TestAsyncRecurring:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncJocall3) -> None:
        recurring = await async_client.transactions.recurring.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        )
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.recurring.with_raw_response.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = await response.parse()
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.recurring.with_streaming_response.create(
            amount=2136.462018591201,
            category="string",
            frequency="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = await response.parse()
            assert recurring is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        recurring = await async_client.transactions.recurring.list()
        assert_matches_type(RecurringListResponse, recurring, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.recurring.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = await response.parse()
        assert_matches_type(RecurringListResponse, recurring, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.recurring.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = await response.parse()
            assert_matches_type(RecurringListResponse, recurring, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cancel(self, async_client: AsyncJocall3) -> None:
        recurring = await async_client.transactions.recurring.cancel(
            "string",
        )
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cancel(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.recurring.with_raw_response.cancel(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        recurring = await response.parse()
        assert recurring is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cancel(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.recurring.with_streaming_response.cancel(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            recurring = await response.parse()
            assert recurring is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cancel(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `recurring_id` but received ''"):
            await async_client.transactions.recurring.with_raw_response.cancel(
                "",
            )
