# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.ai.ads import (
    GenerateCopyResponse,
    GenerateVideoResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestGenerate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_copy(self, client: Jocall3) -> None:
        generate = client.ai.ads.generate.copy(
            product_description="string",
            target_audience="string",
        )
        assert_matches_type(GenerateCopyResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_copy(self, client: Jocall3) -> None:
        response = client.ai.ads.generate.with_raw_response.copy(
            product_description="string",
            target_audience="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = response.parse()
        assert_matches_type(GenerateCopyResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_copy(self, client: Jocall3) -> None:
        with client.ai.ads.generate.with_streaming_response.copy(
            product_description="string",
            target_audience="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = response.parse()
            assert_matches_type(GenerateCopyResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_video(self, client: Jocall3) -> None:
        generate = client.ai.ads.generate.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        )
        assert_matches_type(GenerateVideoResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_video(self, client: Jocall3) -> None:
        response = client.ai.ads.generate.with_raw_response.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = response.parse()
        assert_matches_type(GenerateVideoResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_video(self, client: Jocall3) -> None:
        with client.ai.ads.generate.with_streaming_response.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = response.parse()
            assert_matches_type(GenerateVideoResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncGenerate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_copy(self, async_client: AsyncJocall3) -> None:
        generate = await async_client.ai.ads.generate.copy(
            product_description="string",
            target_audience="string",
        )
        assert_matches_type(GenerateCopyResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_copy(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.ads.generate.with_raw_response.copy(
            product_description="string",
            target_audience="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = await response.parse()
        assert_matches_type(GenerateCopyResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_copy(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.ads.generate.with_streaming_response.copy(
            product_description="string",
            target_audience="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = await response.parse()
            assert_matches_type(GenerateCopyResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_video(self, async_client: AsyncJocall3) -> None:
        generate = await async_client.ai.ads.generate.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        )
        assert_matches_type(GenerateVideoResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_video(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.ads.generate.with_raw_response.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        generate = await response.parse()
        assert_matches_type(GenerateVideoResponse, generate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_video(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.ads.generate.with_streaming_response.video(
            length_seconds=15,
            prompt="string",
            style="Cyberpunk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            generate = await response.parse()
            assert_matches_type(GenerateVideoResponse, generate, path=["response"])

        assert cast(Any, response.is_closed) is True
