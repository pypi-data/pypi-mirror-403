# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.ai.incubator import PitchRetrieveDetailsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPitch:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Jocall3) -> None:
        pitch = client.ai.incubator.pitch.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        )
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Jocall3) -> None:
        response = client.ai.incubator.pitch.with_raw_response.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = response.parse()
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Jocall3) -> None:
        with client.ai.incubator.pitch.with_streaming_response.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = response.parse()
            assert_matches_type(object, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_details(self, client: Jocall3) -> None:
        pitch = client.ai.incubator.pitch.retrieve_details(
            "pitch_qw_synergychain-xyz",
        )
        assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_details(self, client: Jocall3) -> None:
        response = client.ai.incubator.pitch.with_raw_response.retrieve_details(
            "pitch_qw_synergychain-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = response.parse()
        assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_details(self, client: Jocall3) -> None:
        with client.ai.incubator.pitch.with_streaming_response.retrieve_details(
            "pitch_qw_synergychain-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = response.parse()
            assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_details(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `pitch_id` but received ''"):
            client.ai.incubator.pitch.with_raw_response.retrieve_details(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_feedback(self, client: Jocall3) -> None:
        pitch = client.ai.incubator.pitch.update_feedback(
            "pitch_qw_synergychain-xyz",
        )
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_feedback(self, client: Jocall3) -> None:
        response = client.ai.incubator.pitch.with_raw_response.update_feedback(
            "pitch_qw_synergychain-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = response.parse()
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_feedback(self, client: Jocall3) -> None:
        with client.ai.incubator.pitch.with_streaming_response.update_feedback(
            "pitch_qw_synergychain-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = response.parse()
            assert_matches_type(object, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_feedback(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `pitch_id` but received ''"):
            client.ai.incubator.pitch.with_raw_response.update_feedback(
                "",
            )


class TestAsyncPitch:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncJocall3) -> None:
        pitch = await async_client.ai.incubator.pitch.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        )
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.pitch.with_raw_response.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = await response.parse()
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.pitch.with_streaming_response.create(
            financial_projections={
                "seedRoundAmount": 2500000,
                "valuationPreMoney": 10000000,
                "projectionYears": 3,
                "revenueForecast": [500000, 2000000, 6000000],
                "profitabilityEstimate": "Achieve profitability within 18 months.",
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = await response.parse()
            assert_matches_type(object, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_details(self, async_client: AsyncJocall3) -> None:
        pitch = await async_client.ai.incubator.pitch.retrieve_details(
            "pitch_qw_synergychain-xyz",
        )
        assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_details(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.pitch.with_raw_response.retrieve_details(
            "pitch_qw_synergychain-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = await response.parse()
        assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_details(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.pitch.with_streaming_response.retrieve_details(
            "pitch_qw_synergychain-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = await response.parse()
            assert_matches_type(PitchRetrieveDetailsResponse, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_details(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `pitch_id` but received ''"):
            await async_client.ai.incubator.pitch.with_raw_response.retrieve_details(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_feedback(self, async_client: AsyncJocall3) -> None:
        pitch = await async_client.ai.incubator.pitch.update_feedback(
            "pitch_qw_synergychain-xyz",
        )
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_feedback(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.incubator.pitch.with_raw_response.update_feedback(
            "pitch_qw_synergychain-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        pitch = await response.parse()
        assert_matches_type(object, pitch, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_feedback(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.incubator.pitch.with_streaming_response.update_feedback(
            "pitch_qw_synergychain-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            pitch = await response.parse()
            assert_matches_type(object, pitch, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_feedback(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `pitch_id` but received ''"):
            await async_client.ai.incubator.pitch.with_raw_response.update_feedback(
                "",
            )
