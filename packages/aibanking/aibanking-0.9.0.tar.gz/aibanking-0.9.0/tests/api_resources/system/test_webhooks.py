# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.system import WebhookListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestWebhooks:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        webhook = client.system.webhooks.list()
        assert_matches_type(WebhookListResponse, webhook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.system.webhooks.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = response.parse()
        assert_matches_type(WebhookListResponse, webhook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.system.webhooks.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = response.parse()
            assert_matches_type(WebhookListResponse, webhook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_delete(self, client: Jocall3) -> None:
        webhook = client.system.webhooks.delete(
            "string",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_delete(self, client: Jocall3) -> None:
        response = client.system.webhooks.with_raw_response.delete(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = response.parse()
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_delete(self, client: Jocall3) -> None:
        with client.system.webhooks.with_streaming_response.delete(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = response.parse()
            assert webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_delete(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            client.system.webhooks.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register(self, client: Jocall3) -> None:
        webhook = client.system.webhooks.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register_with_all_params(self, client: Jocall3) -> None:
        webhook = client.system.webhooks.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
            secret="string",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_register(self, client: Jocall3) -> None:
        response = client.system.webhooks.with_raw_response.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = response.parse()
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_register(self, client: Jocall3) -> None:
        with client.system.webhooks.with_streaming_response.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = response.parse()
            assert webhook is None

        assert cast(Any, response.is_closed) is True


class TestAsyncWebhooks:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        webhook = await async_client.system.webhooks.list()
        assert_matches_type(WebhookListResponse, webhook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.webhooks.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = await response.parse()
        assert_matches_type(WebhookListResponse, webhook, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.webhooks.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = await response.parse()
            assert_matches_type(WebhookListResponse, webhook, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_delete(self, async_client: AsyncJocall3) -> None:
        webhook = await async_client.system.webhooks.delete(
            "string",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.webhooks.with_raw_response.delete(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = await response.parse()
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.webhooks.with_streaming_response.delete(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = await response.parse()
            assert webhook is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_delete(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `webhook_id` but received ''"):
            await async_client.system.webhooks.with_raw_response.delete(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register(self, async_client: AsyncJocall3) -> None:
        webhook = await async_client.system.webhooks.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register_with_all_params(self, async_client: AsyncJocall3) -> None:
        webhook = await async_client.system.webhooks.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
            secret="string",
        )
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_register(self, async_client: AsyncJocall3) -> None:
        response = await async_client.system.webhooks.with_raw_response.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        webhook = await response.parse()
        assert webhook is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_register(self, async_client: AsyncJocall3) -> None:
        async with async_client.system.webhooks.with_streaming_response.register(
            events=["transaction.created", "login.alert"],
            url="https://QXorJcnKcPtwaBORGsE.lotvPA2bCjZTqn4UyIZX-1yPZ-pK2dDKa7B1wNvGVcmWq9Fk",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            webhook = await response.parse()
            assert webhook is None

        assert cast(Any, response.is_closed) is True
