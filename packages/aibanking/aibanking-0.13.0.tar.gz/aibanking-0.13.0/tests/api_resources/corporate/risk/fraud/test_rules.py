# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate.risk.fraud import (
    RuleListActiveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestRules:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_custom(self, client: Jocall3) -> None:
        rule = client.corporate.risk.fraud.rules.create_custom(
            logic={},
            name="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_custom(self, client: Jocall3) -> None:
        response = client.corporate.risk.fraud.rules.with_raw_response.create_custom(
            logic={},
            name="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = response.parse()
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_custom(self, client: Jocall3) -> None:
        with client.corporate.risk.fraud.rules.with_streaming_response.create_custom(
            logic={},
            name="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = response.parse()
            assert rule is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_active(self, client: Jocall3) -> None:
        rule = client.corporate.risk.fraud.rules.list_active()
        assert_matches_type(RuleListActiveResponse, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_active(self, client: Jocall3) -> None:
        response = client.corporate.risk.fraud.rules.with_raw_response.list_active()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = response.parse()
        assert_matches_type(RuleListActiveResponse, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_active(self, client: Jocall3) -> None:
        with client.corporate.risk.fraud.rules.with_streaming_response.list_active() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = response.parse()
            assert_matches_type(RuleListActiveResponse, rule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_rule(self, client: Jocall3) -> None:
        rule = client.corporate.risk.fraud.rules.update_rule(
            rule_id="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_rule_with_all_params(self, client: Jocall3) -> None:
        rule = client.corporate.risk.fraud.rules.update_rule(
            rule_id="string",
            action="string",
            name="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_rule(self, client: Jocall3) -> None:
        response = client.corporate.risk.fraud.rules.with_raw_response.update_rule(
            rule_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = response.parse()
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_rule(self, client: Jocall3) -> None:
        with client.corporate.risk.fraud.rules.with_streaming_response.update_rule(
            rule_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = response.parse()
            assert rule is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_rule(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rule_id` but received ''"):
            client.corporate.risk.fraud.rules.with_raw_response.update_rule(
                rule_id="",
            )


class TestAsyncRules:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_custom(self, async_client: AsyncJocall3) -> None:
        rule = await async_client.corporate.risk.fraud.rules.create_custom(
            logic={},
            name="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_custom(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.risk.fraud.rules.with_raw_response.create_custom(
            logic={},
            name="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = await response.parse()
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_custom(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.risk.fraud.rules.with_streaming_response.create_custom(
            logic={},
            name="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = await response.parse()
            assert rule is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_active(self, async_client: AsyncJocall3) -> None:
        rule = await async_client.corporate.risk.fraud.rules.list_active()
        assert_matches_type(RuleListActiveResponse, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_active(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.risk.fraud.rules.with_raw_response.list_active()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = await response.parse()
        assert_matches_type(RuleListActiveResponse, rule, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_active(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.risk.fraud.rules.with_streaming_response.list_active() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = await response.parse()
            assert_matches_type(RuleListActiveResponse, rule, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_rule(self, async_client: AsyncJocall3) -> None:
        rule = await async_client.corporate.risk.fraud.rules.update_rule(
            rule_id="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_rule_with_all_params(self, async_client: AsyncJocall3) -> None:
        rule = await async_client.corporate.risk.fraud.rules.update_rule(
            rule_id="string",
            action="string",
            name="string",
        )
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_rule(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.risk.fraud.rules.with_raw_response.update_rule(
            rule_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        rule = await response.parse()
        assert rule is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_rule(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.risk.fraud.rules.with_streaming_response.update_rule(
            rule_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            rule = await response.parse()
            assert rule is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_rule(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `rule_id` but received ''"):
            await async_client.corporate.risk.fraud.rules.with_raw_response.update_rule(
                rule_id="",
            )
