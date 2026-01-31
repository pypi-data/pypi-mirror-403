# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.ai.oracle import (
    SimulateCreateResponse,
    SimulateAdvancedResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSimulate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.create(
            prompt="string",
        )
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_with_all_params(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.create(
            prompt="string",
            parameters={},
        )
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulate.with_raw_response.create(
            prompt="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = response.parse()
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create(self, client: Jocall3) -> None:
        with client.ai.oracle.simulate.with_streaming_response.create(
            prompt="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = response.parse()
            assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_advanced(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        )
        assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_advanced(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulate.with_raw_response.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = response.parse()
        assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_advanced(self, client: Jocall3) -> None:
        with client.ai.oracle.simulate.with_streaming_response.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = response.parse()
            assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_monte_carlo(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        )
        assert simulate is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_monte_carlo(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulate.with_raw_response.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = response.parse()
        assert simulate is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_monte_carlo(self, client: Jocall3) -> None:
        with client.ai.oracle.simulate.with_streaming_response.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = response.parse()
            assert simulate is None

        assert cast(Any, response.is_closed) is True


class TestAsyncSimulate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.create(
            prompt="string",
        )
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.create(
            prompt="string",
            parameters={},
        )
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulate.with_raw_response.create(
            prompt="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = await response.parse()
        assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulate.with_streaming_response.create(
            prompt="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = await response.parse()
            assert_matches_type(SimulateCreateResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_advanced(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        )
        assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_advanced(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulate.with_raw_response.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = await response.parse()
        assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_advanced(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulate.with_streaming_response.advanced(
            prompt="string",
            scenarios=[{"name": "string"}, {"name": "string"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = await response.parse()
            assert_matches_type(SimulateAdvancedResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_monte_carlo(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        )
        assert simulate is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_monte_carlo(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulate.with_raw_response.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = await response.parse()
        assert simulate is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_monte_carlo(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulate.with_streaming_response.monte_carlo(
            iterations=2896,
            variables=["string", "string"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = await response.parse()
            assert simulate is None

        assert cast(Any, response.is_closed) is True
