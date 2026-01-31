# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.lending.decision_get_rationale_response import DecisionGetRationaleResponse

__all__ = ["DecisionsResource", "AsyncDecisionsResource"]


class DecisionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> DecisionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return DecisionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> DecisionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return DecisionsResourceWithStreamingResponse(self)

    def get_rationale(
        self,
        decision_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DecisionGetRationaleResponse:
        """
        Fetches the deep neural logic behind why a loan was approved or denied.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not decision_id:
            raise ValueError(f"Expected a non-empty value for `decision_id` but received {decision_id!r}")
        return self._get(
            f"/lending/decisions/{decision_id}/rationale",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DecisionGetRationaleResponse,
        )


class AsyncDecisionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncDecisionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncDecisionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncDecisionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncDecisionsResourceWithStreamingResponse(self)

    async def get_rationale(
        self,
        decision_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> DecisionGetRationaleResponse:
        """
        Fetches the deep neural logic behind why a loan was approved or denied.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not decision_id:
            raise ValueError(f"Expected a non-empty value for `decision_id` but received {decision_id!r}")
        return await self._get(
            f"/lending/decisions/{decision_id}/rationale",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=DecisionGetRationaleResponse,
        )


class DecisionsResourceWithRawResponse:
    def __init__(self, decisions: DecisionsResource) -> None:
        self._decisions = decisions

        self.get_rationale = to_raw_response_wrapper(
            decisions.get_rationale,
        )


class AsyncDecisionsResourceWithRawResponse:
    def __init__(self, decisions: AsyncDecisionsResource) -> None:
        self._decisions = decisions

        self.get_rationale = async_to_raw_response_wrapper(
            decisions.get_rationale,
        )


class DecisionsResourceWithStreamingResponse:
    def __init__(self, decisions: DecisionsResource) -> None:
        self._decisions = decisions

        self.get_rationale = to_streamed_response_wrapper(
            decisions.get_rationale,
        )


class AsyncDecisionsResourceWithStreamingResponse:
    def __init__(self, decisions: AsyncDecisionsResource) -> None:
        self._decisions = decisions

        self.get_rationale = async_to_streamed_response_wrapper(
            decisions.get_rationale,
        )
