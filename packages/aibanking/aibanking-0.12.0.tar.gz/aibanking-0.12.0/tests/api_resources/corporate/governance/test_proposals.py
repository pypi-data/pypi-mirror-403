# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from aibanking import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from aibanking.types.corporate.governance import (
    ProposalListActiveResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestProposals:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cast_vote(self, client: Jocall3) -> None:
        proposal = client.corporate.governance.proposals.cast_vote(
            proposal_id="string",
            decision="REJECT",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_cast_vote_with_all_params(self, client: Jocall3) -> None:
        proposal = client.corporate.governance.proposals.cast_vote(
            proposal_id="string",
            decision="REJECT",
            comment="string",
            signature="string",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_cast_vote(self, client: Jocall3) -> None:
        response = client.corporate.governance.proposals.with_raw_response.cast_vote(
            proposal_id="string",
            decision="REJECT",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = response.parse()
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_cast_vote(self, client: Jocall3) -> None:
        with client.corporate.governance.proposals.with_streaming_response.cast_vote(
            proposal_id="string",
            decision="REJECT",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = response.parse()
            assert proposal is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_cast_vote(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `proposal_id` but received ''"):
            client.corporate.governance.proposals.with_raw_response.cast_vote(
                proposal_id="",
                decision="REJECT",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_new(self, client: Jocall3) -> None:
        proposal = client.corporate.governance.proposals.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_new_with_all_params(self, client: Jocall3) -> None:
        proposal = client.corporate.governance.proposals.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
            description="string",
            voting_period_hours=24,
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_new(self, client: Jocall3) -> None:
        response = client.corporate.governance.proposals.with_raw_response.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = response.parse()
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_new(self, client: Jocall3) -> None:
        with client.corporate.governance.proposals.with_streaming_response.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = response.parse()
            assert proposal is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_active(self, client: Jocall3) -> None:
        proposal = client.corporate.governance.proposals.list_active()
        assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_active(self, client: Jocall3) -> None:
        response = client.corporate.governance.proposals.with_raw_response.list_active()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = response.parse()
        assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_active(self, client: Jocall3) -> None:
        with client.corporate.governance.proposals.with_streaming_response.list_active() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = response.parse()
            assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncProposals:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cast_vote(self, async_client: AsyncJocall3) -> None:
        proposal = await async_client.corporate.governance.proposals.cast_vote(
            proposal_id="string",
            decision="REJECT",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_cast_vote_with_all_params(self, async_client: AsyncJocall3) -> None:
        proposal = await async_client.corporate.governance.proposals.cast_vote(
            proposal_id="string",
            decision="REJECT",
            comment="string",
            signature="string",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_cast_vote(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.governance.proposals.with_raw_response.cast_vote(
            proposal_id="string",
            decision="REJECT",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = await response.parse()
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_cast_vote(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.governance.proposals.with_streaming_response.cast_vote(
            proposal_id="string",
            decision="REJECT",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = await response.parse()
            assert proposal is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_cast_vote(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `proposal_id` but received ''"):
            await async_client.corporate.governance.proposals.with_raw_response.cast_vote(
                proposal_id="",
                decision="REJECT",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_new(self, async_client: AsyncJocall3) -> None:
        proposal = await async_client.corporate.governance.proposals.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_new_with_all_params(self, async_client: AsyncJocall3) -> None:
        proposal = await async_client.corporate.governance.proposals.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
            description="string",
            voting_period_hours=24,
        )
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_new(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.governance.proposals.with_raw_response.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = await response.parse()
        assert proposal is None

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_new(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.governance.proposals.with_streaming_response.create_new(
            action_type="LARGE_PAYMENT",
            payload={},
            title="string",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = await response.parse()
            assert proposal is None

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_active(self, async_client: AsyncJocall3) -> None:
        proposal = await async_client.corporate.governance.proposals.list_active()
        assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_active(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.governance.proposals.with_raw_response.list_active()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        proposal = await response.parse()
        assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_active(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.governance.proposals.with_streaming_response.list_active() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            proposal = await response.parse()
            assert_matches_type(ProposalListActiveResponse, proposal, path=["response"])

        assert cast(Any, response.is_closed) is True
