# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.marketplace import OfferListOffersResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestOffers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_offers(self, client: Jocall3) -> None:
        offer = client.marketplace.offers.list_offers()
        assert_matches_type(OfferListOffersResponse, offer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_offers(self, client: Jocall3) -> None:
        response = client.marketplace.offers.with_raw_response.list_offers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offer = response.parse()
        assert_matches_type(OfferListOffersResponse, offer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_offers(self, client: Jocall3) -> None:
        with client.marketplace.offers.with_streaming_response.list_offers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offer = response.parse()
            assert_matches_type(OfferListOffersResponse, offer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_redeem_offer(self, client: Jocall3) -> None:
        offer = client.marketplace.offers.redeem_offer(
            "string",
        )
        assert offer is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_redeem_offer(self, client: Jocall3) -> None:
        response = client.marketplace.offers.with_raw_response.redeem_offer(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offer = response.parse()
        assert offer is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_redeem_offer(self, client: Jocall3) -> None:
        with client.marketplace.offers.with_streaming_response.redeem_offer(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offer = response.parse()
            assert offer is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_redeem_offer(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `offer_id` but received ''"):
            client.marketplace.offers.with_raw_response.redeem_offer(
                "",
            )


class TestAsyncOffers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_offers(self, async_client: AsyncJocall3) -> None:
        offer = await async_client.marketplace.offers.list_offers()
        assert_matches_type(OfferListOffersResponse, offer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_offers(self, async_client: AsyncJocall3) -> None:
        response = await async_client.marketplace.offers.with_raw_response.list_offers()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offer = await response.parse()
        assert_matches_type(OfferListOffersResponse, offer, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_offers(self, async_client: AsyncJocall3) -> None:
        async with async_client.marketplace.offers.with_streaming_response.list_offers() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offer = await response.parse()
            assert_matches_type(OfferListOffersResponse, offer, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_redeem_offer(self, async_client: AsyncJocall3) -> None:
        offer = await async_client.marketplace.offers.redeem_offer(
            "string",
        )
        assert offer is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_redeem_offer(self, async_client: AsyncJocall3) -> None:
        response = await async_client.marketplace.offers.with_raw_response.redeem_offer(
            "string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        offer = await response.parse()
        assert offer is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_redeem_offer(self, async_client: AsyncJocall3) -> None:
        async with async_client.marketplace.offers.with_streaming_response.redeem_offer(
            "string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            offer = await response.parse()
            assert offer is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_redeem_offer(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `offer_id` but received ''"):
            await async_client.marketplace.offers.with_raw_response.redeem_offer(
                "",
            )
