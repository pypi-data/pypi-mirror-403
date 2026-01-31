# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ..._compat import cached_property
from .decisions import (
    DecisionsResource,
    AsyncDecisionsResource,
    DecisionsResourceWithRawResponse,
    AsyncDecisionsResourceWithRawResponse,
    DecisionsResourceWithStreamingResponse,
    AsyncDecisionsResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from .applications import (
    ApplicationsResource,
    AsyncApplicationsResource,
    ApplicationsResourceWithRawResponse,
    AsyncApplicationsResourceWithRawResponse,
    ApplicationsResourceWithStreamingResponse,
    AsyncApplicationsResourceWithStreamingResponse,
)

__all__ = ["LendingResource", "AsyncLendingResource"]


class LendingResource(SyncAPIResource):
    @cached_property
    def applications(self) -> ApplicationsResource:
        return ApplicationsResource(self._client)

    @cached_property
    def decisions(self) -> DecisionsResource:
        return DecisionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> LendingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return LendingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> LendingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return LendingResourceWithStreamingResponse(self)


class AsyncLendingResource(AsyncAPIResource):
    @cached_property
    def applications(self) -> AsyncApplicationsResource:
        return AsyncApplicationsResource(self._client)

    @cached_property
    def decisions(self) -> AsyncDecisionsResource:
        return AsyncDecisionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncLendingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncLendingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncLendingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncLendingResourceWithStreamingResponse(self)


class LendingResourceWithRawResponse:
    def __init__(self, lending: LendingResource) -> None:
        self._lending = lending

    @cached_property
    def applications(self) -> ApplicationsResourceWithRawResponse:
        return ApplicationsResourceWithRawResponse(self._lending.applications)

    @cached_property
    def decisions(self) -> DecisionsResourceWithRawResponse:
        return DecisionsResourceWithRawResponse(self._lending.decisions)


class AsyncLendingResourceWithRawResponse:
    def __init__(self, lending: AsyncLendingResource) -> None:
        self._lending = lending

    @cached_property
    def applications(self) -> AsyncApplicationsResourceWithRawResponse:
        return AsyncApplicationsResourceWithRawResponse(self._lending.applications)

    @cached_property
    def decisions(self) -> AsyncDecisionsResourceWithRawResponse:
        return AsyncDecisionsResourceWithRawResponse(self._lending.decisions)


class LendingResourceWithStreamingResponse:
    def __init__(self, lending: LendingResource) -> None:
        self._lending = lending

    @cached_property
    def applications(self) -> ApplicationsResourceWithStreamingResponse:
        return ApplicationsResourceWithStreamingResponse(self._lending.applications)

    @cached_property
    def decisions(self) -> DecisionsResourceWithStreamingResponse:
        return DecisionsResourceWithStreamingResponse(self._lending.decisions)


class AsyncLendingResourceWithStreamingResponse:
    def __init__(self, lending: AsyncLendingResource) -> None:
        self._lending = lending

    @cached_property
    def applications(self) -> AsyncApplicationsResourceWithStreamingResponse:
        return AsyncApplicationsResourceWithStreamingResponse(self._lending.applications)

    @cached_property
    def decisions(self) -> AsyncDecisionsResourceWithStreamingResponse:
        return AsyncDecisionsResourceWithStreamingResponse(self._lending.decisions)
