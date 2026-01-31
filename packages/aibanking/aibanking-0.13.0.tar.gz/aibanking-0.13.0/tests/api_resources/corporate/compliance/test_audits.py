# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking._utils import parse_date
from aibanking.types.corporate.compliance import (
    AuditRequestAuditResponse,
    AuditRetrieveReportResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAudits:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_request_audit(self, client: Jocall3) -> None:
        audit = client.corporate.compliance.audits.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        )
        assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_request_audit(self, client: Jocall3) -> None:
        response = client.corporate.compliance.audits.with_raw_response.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        audit = response.parse()
        assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_request_audit(self, client: Jocall3) -> None:
        with client.corporate.compliance.audits.with_streaming_response.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            audit = response.parse()
            assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_report(self, client: Jocall3) -> None:
        audit = client.corporate.compliance.audits.retrieve_report(
            "string",
        )
        assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_report(self, client: Jocall3) -> None:
        response = client.corporate.compliance.audits.with_raw_response.retrieve_report(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        audit = response.parse()
        assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_report(self, client: Jocall3) -> None:
        with client.corporate.compliance.audits.with_streaming_response.retrieve_report(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            audit = response.parse()
            assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_report(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `audit_id` but received ''"):
            client.corporate.compliance.audits.with_raw_response.retrieve_report(
                "",
            )


class TestAsyncAudits:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_request_audit(self, async_client: AsyncJocall3) -> None:
        audit = await async_client.corporate.compliance.audits.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        )
        assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_request_audit(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.compliance.audits.with_raw_response.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        audit = await response.parse()
        assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_request_audit(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.compliance.audits.with_streaming_response.request_audit(
            audit_scope="string",
            end_date=parse_date("2018-06-28"),
            start_date=parse_date("2006-12-17"),
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            audit = await response.parse()
            assert_matches_type(AuditRequestAuditResponse, audit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_report(self, async_client: AsyncJocall3) -> None:
        audit = await async_client.corporate.compliance.audits.retrieve_report(
            "string",
        )
        assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_report(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.compliance.audits.with_raw_response.retrieve_report(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        audit = await response.parse()
        assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_report(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.compliance.audits.with_streaming_response.retrieve_report(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            audit = await response.parse()
            assert_matches_type(AuditRetrieveReportResponse, audit, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_report(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `audit_id` but received ''"):
            await async_client.corporate.compliance.audits.with_raw_response.retrieve_report(
                "",
            )
