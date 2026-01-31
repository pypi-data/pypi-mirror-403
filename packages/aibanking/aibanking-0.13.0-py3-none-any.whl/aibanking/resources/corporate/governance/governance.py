# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .proposals import (
    ProposalsResource,
    AsyncProposalsResource,
    ProposalsResourceWithRawResponse,
    AsyncProposalsResourceWithRawResponse,
    ProposalsResourceWithStreamingResponse,
    AsyncProposalsResourceWithStreamingResponse,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["GovernanceResource", "AsyncGovernanceResource"]


class GovernanceResource(SyncAPIResource):
    @cached_property
    def proposals(self) -> ProposalsResource:
        return ProposalsResource(self._client)

    @cached_property
    def with_raw_response(self) -> GovernanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return GovernanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> GovernanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return GovernanceResourceWithStreamingResponse(self)


class AsyncGovernanceResource(AsyncAPIResource):
    @cached_property
    def proposals(self) -> AsyncProposalsResource:
        return AsyncProposalsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncGovernanceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncGovernanceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncGovernanceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncGovernanceResourceWithStreamingResponse(self)


class GovernanceResourceWithRawResponse:
    def __init__(self, governance: GovernanceResource) -> None:
        self._governance = governance

    @cached_property
    def proposals(self) -> ProposalsResourceWithRawResponse:
        return ProposalsResourceWithRawResponse(self._governance.proposals)


class AsyncGovernanceResourceWithRawResponse:
    def __init__(self, governance: AsyncGovernanceResource) -> None:
        self._governance = governance

    @cached_property
    def proposals(self) -> AsyncProposalsResourceWithRawResponse:
        return AsyncProposalsResourceWithRawResponse(self._governance.proposals)


class GovernanceResourceWithStreamingResponse:
    def __init__(self, governance: GovernanceResource) -> None:
        self._governance = governance

    @cached_property
    def proposals(self) -> ProposalsResourceWithStreamingResponse:
        return ProposalsResourceWithStreamingResponse(self._governance.proposals)


class AsyncGovernanceResourceWithStreamingResponse:
    def __init__(self, governance: AsyncGovernanceResource) -> None:
        self._governance = governance

    @cached_property
    def proposals(self) -> AsyncProposalsResourceWithStreamingResponse:
        return AsyncProposalsResourceWithStreamingResponse(self._governance.proposals)
