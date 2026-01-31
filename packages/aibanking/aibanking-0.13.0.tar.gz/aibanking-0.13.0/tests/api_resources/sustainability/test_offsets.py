# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOffsets:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_purchase_credits(self, client: Jocall3) -> None:
        offset = client.sustainability.offsets.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_purchase_credits_with_all_params(self, client: Jocall3) -> None:
        offset = client.sustainability.offsets.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
            payment_source_id="string",
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_purchase_credits(self, client: Jocall3) -> None:
        response = client.sustainability.offsets.with_raw_response.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offset = response.parse()
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_purchase_credits(self, client: Jocall3) -> None:
        with client.sustainability.offsets.with_streaming_response.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offset = response.parse()
            assert offset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retire_credits(self, client: Jocall3) -> None:
        offset = client.sustainability.offsets.retire_credits(
            certificate_id="string",
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retire_credits(self, client: Jocall3) -> None:
        response = client.sustainability.offsets.with_raw_response.retire_credits(
            certificate_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offset = response.parse()
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retire_credits(self, client: Jocall3) -> None:
        with client.sustainability.offsets.with_streaming_response.retire_credits(
            certificate_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offset = response.parse()
            assert offset is None

        assert cast(Any, response.is_closed) is True


class TestAsyncOffsets:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_purchase_credits(self, async_client: AsyncJocall3) -> None:
        offset = await async_client.sustainability.offsets.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_purchase_credits_with_all_params(self, async_client: AsyncJocall3) -> None:
        offset = await async_client.sustainability.offsets.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
            payment_source_id="string",
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_purchase_credits(self, async_client: AsyncJocall3) -> None:
        response = await async_client.sustainability.offsets.with_raw_response.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offset = await response.parse()
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_purchase_credits(self, async_client: AsyncJocall3) -> None:
        async with async_client.sustainability.offsets.with_streaming_response.purchase_credits(
            project_id="string",
            tonnes=5219.91816003216,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offset = await response.parse()
            assert offset is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retire_credits(self, async_client: AsyncJocall3) -> None:
        offset = await async_client.sustainability.offsets.retire_credits(
            certificate_id="string",
        )
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retire_credits(self, async_client: AsyncJocall3) -> None:
        response = await async_client.sustainability.offsets.with_raw_response.retire_credits(
            certificate_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offset = await response.parse()
        assert offset is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retire_credits(self, async_client: AsyncJocall3) -> None:
        async with async_client.sustainability.offsets.with_streaming_response.retire_credits(
            certificate_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offset = await response.parse()
            assert offset is None

        assert cast(Any, response.is_closed) is True
