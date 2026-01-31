# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestVerification:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_compare_biometric(self, client: Jocall3) -> None:
        verification = client.system.verification.compare_biometric(
            sample_a="string",
            sample_b="string",
        )
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_compare_biometric(self, client: Jocall3) -> None:
        response = client.system.verification.with_raw_response.compare_biometric(
            sample_a="string",
            sample_b="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = response.parse()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_compare_biometric(self, client: Jocall3) -> None:
        with client.system.verification.with_streaming_response.compare_biometric(
            sample_a="string",
            sample_b="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = response.parse()
            assert verification is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_verify_document(self, client: Jocall3) -> None:
        verification = client.system.verification.verify_document()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_verify_document(self, client: Jocall3) -> None:
        response = client.system.verification.with_raw_response.verify_document()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = response.parse()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_verify_document(self, client: Jocall3) -> None:
        with client.system.verification.with_streaming_response.verify_document() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = response.parse()
            assert verification is None

        assert cast(Any, response.is_closed) is True


class TestAsyncVerification:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_compare_biometric(self, async_client: AsyncJocall3) -> None:
        verification = await async_client.system.verification.compare_biometric(
            sample_a="string",
            sample_b="string",
        )
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_compare_biometric(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.verification.with_raw_response.compare_biometric(
            sample_a="string",
            sample_b="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = await response.parse()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_compare_biometric(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.verification.with_streaming_response.compare_biometric(
            sample_a="string",
            sample_b="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = await response.parse()
            assert verification is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_verify_document(self, async_client: AsyncJocall3) -> None:
        verification = await async_client.system.verification.verify_document()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_verify_document(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.verification.with_raw_response.verify_document()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        verification = await response.parse()
        assert verification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_verify_document(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.verification.with_streaming_response.verify_document() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            verification = await response.parse()
            assert verification is None

        assert cast(Any, response.is_closed) is True
