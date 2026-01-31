# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types import CorporateOnboardResponse
from aibanking._utils import parse_datetime

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCorporate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_onboard(self, client: Jocall3) -> None:
        corporate = client.corporate.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        )
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_onboard_with_all_params(self, client: Jocall3) -> None:
        corporate = client.corporate.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
            beneficial_owners=[
                {
                    "id": "string",
                    "email": "OJsMNh@jTCbAVwjqYWhGnyLe.nddf",
                    "identity_verified": False,
                    "name": "string",
                    "address": {
                        "city": "string",
                        "country": "string",
                        "street": "string",
                        "state": "string",
                        "zip": "string",
                    },
                    "preferences": {"key_0": 5595},
                    "security_status": {
                        "last_login": parse_datetime("2010-09-16T07:13:38.157Z"),
                        "two_factor_enabled": True,
                    },
                },
                {
                    "id": "string",
                    "email": "VrwpDkjpFxkAg10@iRDWTgHNAzKDVkvGQrZ.ecv",
                    "identity_verified": True,
                    "name": "string",
                    "address": {
                        "city": "string",
                        "country": "string",
                        "street": "string",
                        "state": "string",
                        "zip": "string",
                    },
                    "preferences": {"key_0": "string"},
                    "security_status": {
                        "last_login": parse_datetime("1992-06-26T10:35:43.370Z"),
                        "two_factor_enabled": False,
                    },
                },
            ],
        )
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_onboard(self, client: Jocall3) -> None:
        response = client.corporate.with_raw_response.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        corporate = response.parse()
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_onboard(self, client: Jocall3) -> None:
        with client.corporate.with_streaming_response.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            corporate = response.parse()
            assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCorporate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_onboard(self, async_client: AsyncJocall3) -> None:
        corporate = await async_client.corporate.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        )
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_onboard_with_all_params(self, async_client: AsyncJocall3) -> None:
        corporate = await async_client.corporate.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
            beneficial_owners=[
                {
                    "id": "string",
                    "email": "OJsMNh@jTCbAVwjqYWhGnyLe.nddf",
                    "identity_verified": False,
                    "name": "string",
                    "address": {
                        "city": "string",
                        "country": "string",
                        "street": "string",
                        "state": "string",
                        "zip": "string",
                    },
                    "preferences": {"key_0": 5595},
                    "security_status": {
                        "last_login": parse_datetime("2010-09-16T07:13:38.157Z"),
                        "two_factor_enabled": True,
                    },
                },
                {
                    "id": "string",
                    "email": "VrwpDkjpFxkAg10@iRDWTgHNAzKDVkvGQrZ.ecv",
                    "identity_verified": True,
                    "name": "string",
                    "address": {
                        "city": "string",
                        "country": "string",
                        "street": "string",
                        "state": "string",
                        "zip": "string",
                    },
                    "preferences": {"key_0": "string"},
                    "security_status": {
                        "last_login": parse_datetime("1992-06-26T10:35:43.370Z"),
                        "two_factor_enabled": False,
                    },
                },
            ],
        )
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_onboard(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.with_raw_response.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        corporate = await response.parse()
        assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_onboard(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.with_streaming_response.onboard(
            entity_type="CORP",
            jurisdiction="DE",
            legal_name="string",
            tax_id="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            corporate = await response.parse()
            assert_matches_type(CorporateOnboardResponse, corporate, path=["response"])

        assert cast(Any, response.is_closed) is True
