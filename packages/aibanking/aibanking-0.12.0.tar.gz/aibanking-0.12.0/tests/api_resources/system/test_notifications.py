# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.system import NotificationListTemplatesResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestNotifications:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_templates(self, client: Jocall3) -> None:
        notification = client.system.notifications.list_templates()
        assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_templates(self, client: Jocall3) -> None:
        response = client.system.notifications.with_raw_response.list_templates()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        notification = response.parse()
        assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_templates(self, client: Jocall3) -> None:
        with client.system.notifications.with_streaming_response.list_templates() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            notification = response.parse()
            assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_send_push(self, client: Jocall3) -> None:
        notification = client.system.notifications.send_push(
            body="string",
            title="string",
            user_id="string",
        )
        assert notification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_send_push(self, client: Jocall3) -> None:
        response = client.system.notifications.with_raw_response.send_push(
            body="string",
            title="string",
            user_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        notification = response.parse()
        assert notification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_send_push(self, client: Jocall3) -> None:
        with client.system.notifications.with_streaming_response.send_push(
            body="string",
            title="string",
            user_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            notification = response.parse()
            assert notification is None

        assert cast(Any, response.is_closed) is True


class TestAsyncNotifications:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_templates(self, async_client: AsyncJocall3) -> None:
        notification = await async_client.system.notifications.list_templates()
        assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_templates(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.notifications.with_raw_response.list_templates()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        notification = await response.parse()
        assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_templates(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.notifications.with_streaming_response.list_templates() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            notification = await response.parse()
            assert_matches_type(NotificationListTemplatesResponse, notification, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_send_push(self, async_client: AsyncJocall3) -> None:
        notification = await async_client.system.notifications.send_push(
            body="string",
            title="string",
            user_id="string",
        )
        assert notification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_send_push(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.notifications.with_raw_response.send_push(
            body="string",
            title="string",
            user_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        notification = await response.parse()
        assert notification is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_send_push(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.notifications.with_streaming_response.send_push(
            body="string",
            title="string",
            user_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            notification = await response.parse()
            assert notification is None

        assert cast(Any, response.is_closed) is True
