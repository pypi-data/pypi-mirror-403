# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.ai import IncubatorValidateResponse, IncubatorRetrievePitchesResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestIncubator:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_pitches(self, client: Jocall3) -> None:
        incubator = client.ai.incubator.retrieve_pitches()
        assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_pitches(self, client: Jocall3) -> None:
        response = client.ai.incubator.with_raw_response.retrieve_pitches()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        incubator = response.parse()
        assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_pitches(self, client: Jocall3) -> None:
        with client.ai.incubator.with_streaming_response.retrieve_pitches() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            incubator = response.parse()
            assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_validate(self, client: Jocall3) -> None:
        incubator = client.ai.incubator.validate(
            concept="string",
        )
        assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_validate(self, client: Jocall3) -> None:
        response = client.ai.incubator.with_raw_response.validate(
            concept="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        incubator = response.parse()
        assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_validate(self, client: Jocall3) -> None:
        with client.ai.incubator.with_streaming_response.validate(
            concept="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            incubator = response.parse()
            assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncIncubator:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_pitches(self, async_client: AsyncJocall3) -> None:
        incubator = await async_client.ai.incubator.retrieve_pitches()
        assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_pitches(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.with_raw_response.retrieve_pitches()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        incubator = await response.parse()
        assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_pitches(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.with_streaming_response.retrieve_pitches() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            incubator = await response.parse()
            assert_matches_type(IncubatorRetrievePitchesResponse, incubator, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_validate(self, async_client: AsyncJocall3) -> None:
        incubator = await async_client.ai.incubator.validate(
            concept="string",
        )
        assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_validate(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.with_raw_response.validate(
            concept="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        incubator = await response.parse()
        assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_validate(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.with_streaming_response.validate(
            concept="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            incubator = await response.parse()
            assert_matches_type(IncubatorValidateResponse, incubator, path=["response"])

        assert cast(Any, response.is_closed) is True
