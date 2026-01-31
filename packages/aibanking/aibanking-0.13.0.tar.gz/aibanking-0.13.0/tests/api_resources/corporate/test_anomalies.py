# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate import AnomalyListDetectedResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAnomalies:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_detected(self, client: Jocall3) -> None:
        anomaly = client.corporate.anomalies.list_detected()
        assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_detected(self, client: Jocall3) -> None:
        response = client.corporate.anomalies.with_raw_response.list_detected()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        anomaly = response.parse()
        assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_detected(self, client: Jocall3) -> None:
        with client.corporate.anomalies.with_streaming_response.list_detected() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            anomaly = response.parse()
            assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_status(self, client: Jocall3) -> None:
        anomaly = client.corporate.anomalies.update_status(
            anomaly_id="string",
            status="investigating",
        )
        assert anomaly is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_status(self, client: Jocall3) -> None:
        response = client.corporate.anomalies.with_raw_response.update_status(
            anomaly_id="string",
            status="investigating",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        anomaly = response.parse()
        assert anomaly is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_status(self, client: Jocall3) -> None:
        with client.corporate.anomalies.with_streaming_response.update_status(
            anomaly_id="string",
            status="investigating",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            anomaly = response.parse()
            assert anomaly is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_status(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `anomaly_id` but received ''"):
            client.corporate.anomalies.with_raw_response.update_status(
                anomaly_id="",
                status="investigating",
            )


class TestAsyncAnomalies:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_detected(self, async_client: AsyncJocall3) -> None:
        anomaly = await async_client.corporate.anomalies.list_detected()
        assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_detected(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.anomalies.with_raw_response.list_detected()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        anomaly = await response.parse()
        assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_detected(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.anomalies.with_streaming_response.list_detected() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            anomaly = await response.parse()
            assert_matches_type(AnomalyListDetectedResponse, anomaly, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_status(self, async_client: AsyncJocall3) -> None:
        anomaly = await async_client.corporate.anomalies.update_status(
            anomaly_id="string",
            status="investigating",
        )
        assert anomaly is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.anomalies.with_raw_response.update_status(
            anomaly_id="string",
            status="investigating",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        anomaly = await response.parse()
        assert anomaly is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.anomalies.with_streaming_response.update_status(
            anomaly_id="string",
            status="investigating",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            anomaly = await response.parse()
            assert anomaly is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_status(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `anomaly_id` but received ''"):
            await async_client.corporate.anomalies.with_raw_response.update_status(
                anomaly_id="",
                status="investigating",
            )
