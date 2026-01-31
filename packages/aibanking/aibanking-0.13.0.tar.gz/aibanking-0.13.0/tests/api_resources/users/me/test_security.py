# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.users.me import (
    SecurityRotateKeysResponse,
    SecurityRetrieveLogResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSecurity:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_log(self, client: Jocall3) -> None:
        security = client.users.me.security.retrieve_log()
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_log_with_all_params(self, client: Jocall3) -> None:
        security = client.users.me.security.retrieve_log(
            limit=0,
            offset=0,
        )
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_log(self, client: Jocall3) -> None:
        response = client.users.me.security.with_raw_response.retrieve_log()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        security = response.parse()
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_log(self, client: Jocall3) -> None:
        with client.users.me.security.with_streaming_response.retrieve_log() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            security = response.parse()
            assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_rotate_keys(self, client: Jocall3) -> None:
        security = client.users.me.security.rotate_keys()
        assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_rotate_keys(self, client: Jocall3) -> None:
        response = client.users.me.security.with_raw_response.rotate_keys()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        security = response.parse()
        assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_rotate_keys(self, client: Jocall3) -> None:
        with client.users.me.security.with_streaming_response.rotate_keys() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            security = response.parse()
            assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSecurity:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_log(self, async_client: AsyncJocall3) -> None:
        security = await async_client.users.me.security.retrieve_log()
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_log_with_all_params(self, async_client: AsyncJocall3) -> None:
        security = await async_client.users.me.security.retrieve_log(
            limit=0,
            offset=0,
        )
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_log(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.security.with_raw_response.retrieve_log()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        security = await response.parse()
        assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_log(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.security.with_streaming_response.retrieve_log() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            security = await response.parse()
            assert_matches_type(SecurityRetrieveLogResponse, security, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_rotate_keys(self, async_client: AsyncJocall3) -> None:
        security = await async_client.users.me.security.rotate_keys()
        assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_rotate_keys(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.security.with_raw_response.rotate_keys()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        security = await response.parse()
        assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_rotate_keys(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.security.with_streaming_response.rotate_keys() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            security = await response.parse()
            assert_matches_type(SecurityRotateKeysResponse, security, path=["response"])

        assert cast(Any, response.is_closed) is True
