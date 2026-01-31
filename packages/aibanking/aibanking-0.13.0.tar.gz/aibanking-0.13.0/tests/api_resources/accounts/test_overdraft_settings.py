# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.accounts import (
    OverdraftSettingRetrieveOverdraftSettingsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOverdraftSettings:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_overdraft_settings(self, client: Jocall3) -> None:
        overdraft_setting = client.accounts.overdraft_settings.retrieve_overdraft_settings(
            "string",
        )
        assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_overdraft_settings(self, client: Jocall3) -> None:
        response = client.accounts.overdraft_settings.with_raw_response.retrieve_overdraft_settings(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        overdraft_setting = response.parse()
        assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_overdraft_settings(self, client: Jocall3) -> None:
        with client.accounts.overdraft_settings.with_streaming_response.retrieve_overdraft_settings(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            overdraft_setting = response.parse()
            assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_overdraft_settings(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.overdraft_settings.with_raw_response.retrieve_overdraft_settings(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_overdraft_settings(self, client: Jocall3) -> None:
        overdraft_setting = client.accounts.overdraft_settings.update_overdraft_settings(
            account_id="string",
        )
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_overdraft_settings_with_all_params(self, client: Jocall3) -> None:
        overdraft_setting = client.accounts.overdraft_settings.update_overdraft_settings(
            account_id="string",
            enabled=True,
            limit=2541.91725603093,
        )
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_overdraft_settings(self, client: Jocall3) -> None:
        response = client.accounts.overdraft_settings.with_raw_response.update_overdraft_settings(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        overdraft_setting = response.parse()
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_overdraft_settings(self, client: Jocall3) -> None:
        with client.accounts.overdraft_settings.with_streaming_response.update_overdraft_settings(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            overdraft_setting = response.parse()
            assert overdraft_setting is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_overdraft_settings(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            client.accounts.overdraft_settings.with_raw_response.update_overdraft_settings(
                account_id="",
            )


class TestAsyncOverdraftSettings:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        overdraft_setting = await async_client.accounts.overdraft_settings.retrieve_overdraft_settings(
            "string",
        )
        assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.overdraft_settings.with_raw_response.retrieve_overdraft_settings(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        overdraft_setting = await response.parse()
        assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.overdraft_settings.with_streaming_response.retrieve_overdraft_settings(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            overdraft_setting = await response.parse()
            assert_matches_type(OverdraftSettingRetrieveOverdraftSettingsResponse, overdraft_setting, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.overdraft_settings.with_raw_response.retrieve_overdraft_settings(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        overdraft_setting = await async_client.accounts.overdraft_settings.update_overdraft_settings(
            account_id="string",
        )
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_overdraft_settings_with_all_params(self, async_client: AsyncJocall3) -> None:
        overdraft_setting = await async_client.accounts.overdraft_settings.update_overdraft_settings(
            account_id="string",
            enabled=True,
            limit=2541.91725603093,
        )
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        response = await async_client.accounts.overdraft_settings.with_raw_response.update_overdraft_settings(
            account_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        overdraft_setting = await response.parse()
        assert overdraft_setting is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        async with async_client.accounts.overdraft_settings.with_streaming_response.update_overdraft_settings(
            account_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            overdraft_setting = await response.parse()
            assert overdraft_setting is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_overdraft_settings(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `account_id` but received ''"):
            await async_client.accounts.overdraft_settings.with_raw_response.update_overdraft_settings(
                account_id="",
            )
