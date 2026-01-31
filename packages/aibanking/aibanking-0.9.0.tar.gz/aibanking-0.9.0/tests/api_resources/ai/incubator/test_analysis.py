# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.ai.incubator import (
    AnalysisSwotResponse,
    AnalysisCompetitorsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAnalysis:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_competitors(self, client: Jocall3) -> None:
        analysis = client.ai.incubator.analysis.competitors(
            industry="string",
            niche="string",
        )
        assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_competitors(self, client: Jocall3) -> None:
        response = client.ai.incubator.analysis.with_raw_response.competitors(
            industry="string",
            niche="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_competitors(self, client: Jocall3) -> None:
        with client.ai.incubator.analysis.with_streaming_response.competitors(
            industry="string",
            niche="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_swot(self, client: Jocall3) -> None:
        analysis = client.ai.incubator.analysis.swot(
            business_context="string",
        )
        assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_swot(self, client: Jocall3) -> None:
        response = client.ai.incubator.analysis.with_raw_response.swot(
            business_context="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = response.parse()
        assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_swot(self, client: Jocall3) -> None:
        with client.ai.incubator.analysis.with_streaming_response.swot(
            business_context="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = response.parse()
            assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAnalysis:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_competitors(self, async_client: AsyncJocall3) -> None:
        analysis = await async_client.ai.incubator.analysis.competitors(
            industry="string",
            niche="string",
        )
        assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_competitors(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.analysis.with_raw_response.competitors(
            industry="string",
            niche="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_competitors(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.analysis.with_streaming_response.competitors(
            industry="string",
            niche="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(AnalysisCompetitorsResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_swot(self, async_client: AsyncJocall3) -> None:
        analysis = await async_client.ai.incubator.analysis.swot(
            business_context="string",
        )
        assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_swot(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.analysis.with_raw_response.swot(
            business_context="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        analysis = await response.parse()
        assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_swot(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.analysis.with_streaming_response.swot(
            business_context="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            analysis = await response.parse()
            assert_matches_type(AnalysisSwotResponse, analysis, path=["response"])

        assert cast(Any, response.is_closed) is True
