# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.system import SandboxSimulateErrorResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSandbox:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_reset(self, client: Jocall3) -> None:
        sandbox = client.system.sandbox.reset()
        assert sandbox is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_reset(self, client: Jocall3) -> None:
        response = client.system.sandbox.with_raw_response.reset()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert sandbox is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_reset(self, client: Jocall3) -> None:
        with client.system.sandbox.with_streaming_response.reset() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert sandbox is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_simulate_error(self, client: Jocall3) -> None:
        sandbox = client.system.sandbox.simulate_error(
            error_code=500,
        )
        assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_simulate_error(self, client: Jocall3) -> None:
        response = client.system.sandbox.with_raw_response.simulate_error(
            error_code=500,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = response.parse()
        assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_simulate_error(self, client: Jocall3) -> None:
        with client.system.sandbox.with_streaming_response.simulate_error(
            error_code=500,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = response.parse()
            assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSandbox:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_reset(self, async_client: AsyncJocall3) -> None:
        sandbox = await async_client.system.sandbox.reset()
        assert sandbox is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_reset(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.sandbox.with_raw_response.reset()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert sandbox is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_reset(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.sandbox.with_streaming_response.reset() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert sandbox is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_simulate_error(self, async_client: AsyncJocall3) -> None:
        sandbox = await async_client.system.sandbox.simulate_error(
            error_code=500,
        )
        assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_simulate_error(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.sandbox.with_raw_response.simulate_error(
            error_code=500,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        sandbox = await response.parse()
        assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_simulate_error(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.sandbox.with_streaming_response.simulate_error(
            error_code=500,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            sandbox = await response.parse()
            assert_matches_type(SandboxSimulateErrorResponse, sandbox, path=["response"])

        assert cast(Any, response.is_closed) is True
