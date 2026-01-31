# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking._utils import parse_date
from aibanking.types.corporate import (
    ComplianceScreenPepResponse,
    ComplianceScreenMediaResponse,
    ComplianceScreenSanctionsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCompliance:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_media(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_media(
            query="string",
        )
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_media_with_all_params(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_media(
            query="string",
            depth="shallow",
        )
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_screen_media(self, client: Jocall3) -> None:
        response = client.corporate.compliance.with_raw_response.screen_media(
            query="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = response.parse()
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_screen_media(self, client: Jocall3) -> None:
        with client.corporate.compliance.with_streaming_response.screen_media(
            query="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = response.parse()
            assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_pep(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_pep(
            full_name="string",
        )
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_pep_with_all_params(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_pep(
            full_name="string",
            dob=parse_date("1959-07-22"),
        )
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_screen_pep(self, client: Jocall3) -> None:
        response = client.corporate.compliance.with_raw_response.screen_pep(
            full_name="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = response.parse()
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_screen_pep(self, client: Jocall3) -> None:
        with client.corporate.compliance.with_streaming_response.screen_pep(
            full_name="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = response.parse()
            assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_sanctions(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_sanctions(
            entities=[{}, {}],
        )
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_screen_sanctions_with_all_params(self, client: Jocall3) -> None:
        compliance = client.corporate.compliance.screen_sanctions(
            entities=[
                {
                    "country": "string",
                    "name": "string",
                },
                {
                    "country": "string",
                    "name": "string",
                },
            ],
            check_type="enhanced_due_diligence",
        )
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_screen_sanctions(self, client: Jocall3) -> None:
        response = client.corporate.compliance.with_raw_response.screen_sanctions(
            entities=[{}, {}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = response.parse()
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_screen_sanctions(self, client: Jocall3) -> None:
        with client.corporate.compliance.with_streaming_response.screen_sanctions(
            entities=[{}, {}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = response.parse()
            assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncCompliance:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_media(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_media(
            query="string",
        )
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_media_with_all_params(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_media(
            query="string",
            depth="shallow",
        )
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_screen_media(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.compliance.with_raw_response.screen_media(
            query="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = await response.parse()
        assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_screen_media(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.compliance.with_streaming_response.screen_media(
            query="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = await response.parse()
            assert_matches_type(ComplianceScreenMediaResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_pep(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_pep(
            full_name="string",
        )
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_pep_with_all_params(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_pep(
            full_name="string",
            dob=parse_date("1959-07-22"),
        )
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_screen_pep(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.compliance.with_raw_response.screen_pep(
            full_name="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = await response.parse()
        assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_screen_pep(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.compliance.with_streaming_response.screen_pep(
            full_name="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = await response.parse()
            assert_matches_type(ComplianceScreenPepResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_sanctions(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_sanctions(
            entities=[{}, {}],
        )
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_screen_sanctions_with_all_params(self, async_client: AsyncJocall3) -> None:
        compliance = await async_client.corporate.compliance.screen_sanctions(
            entities=[
                {
                    "country": "string",
                    "name": "string",
                },
                {
                    "country": "string",
                    "name": "string",
                },
            ],
            check_type="enhanced_due_diligence",
        )
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_screen_sanctions(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.compliance.with_raw_response.screen_sanctions(
            entities=[{}, {}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        compliance = await response.parse()
        assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_screen_sanctions(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.compliance.with_streaming_response.screen_sanctions(
            entities=[{}, {}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            compliance = await response.parse()
            assert_matches_type(ComplianceScreenSanctionsResponse, compliance, path=["response"])

        assert cast(Any, response.is_closed) is True
