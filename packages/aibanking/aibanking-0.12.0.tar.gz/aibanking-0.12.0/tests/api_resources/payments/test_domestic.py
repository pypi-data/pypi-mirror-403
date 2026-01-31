# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDomestic:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_ach(self, client: Jocall3) -> None:
        domestic = client.payments.domestic.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_ach(self, client: Jocall3) -> None:
        response = client.payments.domestic.with_raw_response.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_ach(self, client: Jocall3) -> None:
        with client.payments.domestic.with_streaming_response.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_rtp(self, client: Jocall3) -> None:
        domestic = client.payments.domestic.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_rtp(self, client: Jocall3) -> None:
        response = client.payments.domestic.with_raw_response.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_rtp(self, client: Jocall3) -> None:
        with client.payments.domestic.with_streaming_response.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_execute_wire(self, client: Jocall3) -> None:
        domestic = client.payments.domestic.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_execute_wire(self, client: Jocall3) -> None:
        response = client.payments.domestic.with_raw_response.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_execute_wire(self, client: Jocall3) -> None:
        with client.payments.domestic.with_streaming_response.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True


class TestAsyncDomestic:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_ach(self, async_client: AsyncJocall3) -> None:
        domestic = await async_client.payments.domestic.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_ach(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.domestic.with_raw_response.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = await response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_ach(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.domestic.with_streaming_response.execute_ach(
            account="string",
            amount=9587.708408938319,
            routing="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = await response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_rtp(self, async_client: AsyncJocall3) -> None:
        domestic = await async_client.payments.domestic.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_rtp(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.domestic.with_raw_response.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = await response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_rtp(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.domestic.with_streaming_response.execute_rtp(
            amount=856.3350923839752,
            recipient_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = await response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_execute_wire(self, async_client: AsyncJocall3) -> None:
        domestic = await async_client.payments.domestic.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_execute_wire(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.domestic.with_raw_response.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        domestic = await response.parse()
        assert domestic is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_execute_wire(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.domestic.with_streaming_response.execute_wire(
            account="string",
            amount=9587.708408938319,
            routing="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            domestic = await response.parse()
            assert domestic is None

        assert cast(Any, response.is_closed) is True
