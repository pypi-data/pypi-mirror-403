# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types import SustainabilityRetrieveCarbonFootprintResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSustainability:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_carbon_footprint(self, client: Jocall3) -> None:
        sustainability = client.sustainability.retrieve_carbon_footprint()
        assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_carbon_footprint(self, client: Jocall3) -> None:
        response = client.sustainability.with_raw_response.retrieve_carbon_footprint()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sustainability = response.parse()
        assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_carbon_footprint(self, client: Jocall3) -> None:
        with client.sustainability.with_streaming_response.retrieve_carbon_footprint() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sustainability = response.parse()
            assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSustainability:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_carbon_footprint(self, async_client: AsyncJocall3) -> None:
        sustainability = await async_client.sustainability.retrieve_carbon_footprint()
        assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_carbon_footprint(self, async_client: AsyncJocall3) -> None:
        response = await async_client.sustainability.with_raw_response.retrieve_carbon_footprint()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sustainability = await response.parse()
        assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_carbon_footprint(self, async_client: AsyncJocall3) -> None:
        async with async_client.sustainability.with_streaming_response.retrieve_carbon_footprint() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sustainability = await response.parse()
            assert_matches_type(SustainabilityRetrieveCarbonFootprintResponse, sustainability, path=["response"])

        assert cast(Any, response.is_closed) is True
