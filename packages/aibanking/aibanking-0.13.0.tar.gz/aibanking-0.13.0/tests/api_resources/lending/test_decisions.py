# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.lending import DecisionGetRationaleResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestDecisions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_rationale(self, client: Jocall3) -> None:
        decision = client.lending.decisions.get_rationale(
            "string",
        )
        assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_rationale(self, client: Jocall3) -> None:
        response = client.lending.decisions.with_raw_response.get_rationale(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        decision = response.parse()
        assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_rationale(self, client: Jocall3) -> None:
        with client.lending.decisions.with_streaming_response.get_rationale(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            decision = response.parse()
            assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_rationale(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `decision_id` but received ''"):
            client.lending.decisions.with_raw_response.get_rationale(
                "",
            )


class TestAsyncDecisions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_rationale(self, async_client: AsyncJocall3) -> None:
        decision = await async_client.lending.decisions.get_rationale(
            "string",
        )
        assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_rationale(self, async_client: AsyncJocall3) -> None:
        response = await async_client.lending.decisions.with_raw_response.get_rationale(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        decision = await response.parse()
        assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_rationale(self, async_client: AsyncJocall3) -> None:
        async with async_client.lending.decisions.with_streaming_response.get_rationale(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            decision = await response.parse()
            assert_matches_type(DecisionGetRationaleResponse, decision, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_rationale(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `decision_id` but received ''"):
            await async_client.lending.decisions.with_raw_response.get_rationale(
                "",
            )
