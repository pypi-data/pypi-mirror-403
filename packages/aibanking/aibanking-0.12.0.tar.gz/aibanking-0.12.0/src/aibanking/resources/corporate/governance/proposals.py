# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ...._types import Body, Omit, Query, Headers, NoneType, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.corporate.governance import proposal_cast_vote_params, proposal_create_new_params
from ....types.corporate.governance.proposal_list_active_response import ProposalListActiveResponse

__all__ = ["ProposalsResource", "AsyncProposalsResource"]


class ProposalsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ProposalsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return ProposalsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ProposalsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return ProposalsResourceWithStreamingResponse(self)

    def cast_vote(
        self,
        proposal_id: str,
        *,
        decision: Literal["APPROVE", "REJECT"],
        comment: str | Omit = omit,
        signature: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Cast Vote or Sign Transaction

        Args:
          signature: Cryptographic signature if required

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not proposal_id:
            raise ValueError(f"Expected a non-empty value for `proposal_id` but received {proposal_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/corporate/governance/proposals/{proposal_id}/vote",
            body=maybe_transform(
                {
                    "decision": decision,
                    "comment": comment,
                    "signature": signature,
                },
                proposal_cast_vote_params.ProposalCastVoteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def create_new(
        self,
        *,
        action_type: Literal["TRANSFER_LIMIT_CHANGE", "NEW_ADMIN", "LARGE_PAYMENT"],
        payload: object,
        title: str,
        description: str | Omit = omit,
        voting_period_hours: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create New Multi-sig Financial Proposal

        Args:
          payload: The raw action data to be executed upon approval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/corporate/governance/proposals",
            body=maybe_transform(
                {
                    "action_type": action_type,
                    "payload": payload,
                    "title": title,
                    "description": description,
                    "voting_period_hours": voting_period_hours,
                },
                proposal_create_new_params.ProposalCreateNewParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def list_active(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProposalListActiveResponse:
        """List Active Governance Proposals"""
        return self._get(
            "/corporate/governance/proposals",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProposalListActiveResponse,
        )


class AsyncProposalsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncProposalsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncProposalsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncProposalsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncProposalsResourceWithStreamingResponse(self)

    async def cast_vote(
        self,
        proposal_id: str,
        *,
        decision: Literal["APPROVE", "REJECT"],
        comment: str | Omit = omit,
        signature: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Cast Vote or Sign Transaction

        Args:
          signature: Cryptographic signature if required

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not proposal_id:
            raise ValueError(f"Expected a non-empty value for `proposal_id` but received {proposal_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/corporate/governance/proposals/{proposal_id}/vote",
            body=await async_maybe_transform(
                {
                    "decision": decision,
                    "comment": comment,
                    "signature": signature,
                },
                proposal_cast_vote_params.ProposalCastVoteParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def create_new(
        self,
        *,
        action_type: Literal["TRANSFER_LIMIT_CHANGE", "NEW_ADMIN", "LARGE_PAYMENT"],
        payload: object,
        title: str,
        description: str | Omit = omit,
        voting_period_hours: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Create New Multi-sig Financial Proposal

        Args:
          payload: The raw action data to be executed upon approval

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/corporate/governance/proposals",
            body=await async_maybe_transform(
                {
                    "action_type": action_type,
                    "payload": payload,
                    "title": title,
                    "description": description,
                    "voting_period_hours": voting_period_hours,
                },
                proposal_create_new_params.ProposalCreateNewParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def list_active(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ProposalListActiveResponse:
        """List Active Governance Proposals"""
        return await self._get(
            "/corporate/governance/proposals",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ProposalListActiveResponse,
        )


class ProposalsResourceWithRawResponse:
    def __init__(self, proposals: ProposalsResource) -> None:
        self._proposals = proposals

        self.cast_vote = to_raw_response_wrapper(
            proposals.cast_vote,
        )
        self.create_new = to_raw_response_wrapper(
            proposals.create_new,
        )
        self.list_active = to_raw_response_wrapper(
            proposals.list_active,
        )


class AsyncProposalsResourceWithRawResponse:
    def __init__(self, proposals: AsyncProposalsResource) -> None:
        self._proposals = proposals

        self.cast_vote = async_to_raw_response_wrapper(
            proposals.cast_vote,
        )
        self.create_new = async_to_raw_response_wrapper(
            proposals.create_new,
        )
        self.list_active = async_to_raw_response_wrapper(
            proposals.list_active,
        )


class ProposalsResourceWithStreamingResponse:
    def __init__(self, proposals: ProposalsResource) -> None:
        self._proposals = proposals

        self.cast_vote = to_streamed_response_wrapper(
            proposals.cast_vote,
        )
        self.create_new = to_streamed_response_wrapper(
            proposals.create_new,
        )
        self.list_active = to_streamed_response_wrapper(
            proposals.list_active,
        )


class AsyncProposalsResourceWithStreamingResponse:
    def __init__(self, proposals: AsyncProposalsResource) -> None:
        self._proposals = proposals

        self.cast_vote = async_to_streamed_response_wrapper(
            proposals.cast_vote,
        )
        self.create_new = async_to_streamed_response_wrapper(
            proposals.create_new,
        )
        self.list_active = async_to_streamed_response_wrapper(
            proposals.list_active,
        )
