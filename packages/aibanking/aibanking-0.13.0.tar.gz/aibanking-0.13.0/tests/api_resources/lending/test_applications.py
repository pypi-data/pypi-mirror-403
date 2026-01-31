# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.lending import ApplicationSubmitResponse, ApplicationTrackStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestApplications:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit(self, client: Jocall3) -> None:
        application = client.lending.applications.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        )
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_submit_with_all_params(self, client: Jocall3) -> None:
        application = client.lending.applications.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
                "tenure_months": 5190,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
            assets=[{}],
            collateral_id="string",
            liabilities=[{}],
        )
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_submit(self, client: Jocall3) -> None:
        response = client.lending.applications.with_raw_response.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        application = response.parse()
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_submit(self, client: Jocall3) -> None:
        with client.lending.applications.with_streaming_response.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            application = response.parse()
            assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_track_status(self, client: Jocall3) -> None:
        application = client.lending.applications.track_status(
            "string",
        )
        assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_track_status(self, client: Jocall3) -> None:
        response = client.lending.applications.with_raw_response.track_status(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        application = response.parse()
        assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_track_status(self, client: Jocall3) -> None:
        with client.lending.applications.with_streaming_response.track_status(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            application = response.parse()
            assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_track_status(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `app_id` but received ''"):
            client.lending.applications.with_raw_response.track_status(
                "",
            )


class TestAsyncApplications:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit(self, async_client: AsyncJocall3) -> None:
        application = await async_client.lending.applications.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        )
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_submit_with_all_params(self, async_client: AsyncJocall3) -> None:
        application = await async_client.lending.applications.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
                "tenure_months": 5190,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
            assets=[{}],
            collateral_id="string",
            liabilities=[{}],
        )
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_submit(self, async_client: AsyncJocall3) -> None:
        response = await async_client.lending.applications.with_raw_response.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        application = await response.parse()
        assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_submit(self, async_client: AsyncJocall3) -> None:
        async with async_client.lending.applications.with_streaming_response.submit(
            amount=3369.535449899852,
            employment_data={
                "employer": "string",
                "monthly_income": 22.870503510263873,
            },
            loan_type="BUSINESS_EXPANSION",
            term_months=7703,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            application = await response.parse()
            assert_matches_type(ApplicationSubmitResponse, application, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_track_status(self, async_client: AsyncJocall3) -> None:
        application = await async_client.lending.applications.track_status(
            "string",
        )
        assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_track_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.lending.applications.with_raw_response.track_status(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        application = await response.parse()
        assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_track_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.lending.applications.with_streaming_response.track_status(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            application = await response.parse()
            assert_matches_type(ApplicationTrackStatusResponse, application, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_track_status(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `app_id` but received ''"):
            await async_client.lending.applications.with_raw_response.track_status(
                "",
            )
