# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types import SystemGetStatusResponse, SystemGetAuditLogsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSystem:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_audit_logs(self, client: Jocall3) -> None:
        system = client.system.get_audit_logs()
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_audit_logs_with_all_params(self, client: Jocall3) -> None:
        system = client.system.get_audit_logs(
            actor_id="actorId",
            limit=0,
            offset=0,
        )
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_audit_logs(self, client: Jocall3) -> None:
        response = client.system.with_raw_response.get_audit_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        system = response.parse()
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_audit_logs(self, client: Jocall3) -> None:
        with client.system.with_streaming_response.get_audit_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            system = response.parse()
            assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_status(self, client: Jocall3) -> None:
        system = client.system.get_status()
        assert_matches_type(SystemGetStatusResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_status(self, client: Jocall3) -> None:
        response = client.system.with_raw_response.get_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        system = response.parse()
        assert_matches_type(SystemGetStatusResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_status(self, client: Jocall3) -> None:
        with client.system.with_streaming_response.get_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            system = response.parse()
            assert_matches_type(SystemGetStatusResponse, system, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSystem:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_audit_logs(self, async_client: AsyncJocall3) -> None:
        system = await async_client.system.get_audit_logs()
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_audit_logs_with_all_params(self, async_client: AsyncJocall3) -> None:
        system = await async_client.system.get_audit_logs(
            actor_id="actorId",
            limit=0,
            offset=0,
        )
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_audit_logs(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.with_raw_response.get_audit_logs()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        system = await response.parse()
        assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_audit_logs(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.with_streaming_response.get_audit_logs() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            system = await response.parse()
            assert_matches_type(SystemGetAuditLogsResponse, system, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_status(self, async_client: AsyncJocall3) -> None:
        system = await async_client.system.get_status()
        assert_matches_type(SystemGetStatusResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.with_raw_response.get_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        system = await response.parse()
        assert_matches_type(SystemGetStatusResponse, system, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.with_streaming_response.get_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            system = await response.parse()
            assert_matches_type(SystemGetStatusResponse, system, path=["response"])

        assert cast(Any, response.is_closed) is True
