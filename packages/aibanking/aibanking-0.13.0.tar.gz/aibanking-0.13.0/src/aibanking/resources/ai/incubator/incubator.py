# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .pitch import (
    PitchResource,
    AsyncPitchResource,
    PitchResourceWithRawResponse,
    AsyncPitchResourceWithRawResponse,
    PitchResourceWithStreamingResponse,
    AsyncPitchResourceWithStreamingResponse,
)
from .analysis import (
    AnalysisResource,
    AsyncAnalysisResource,
    AnalysisResourceWithRawResponse,
    AsyncAnalysisResourceWithRawResponse,
    AnalysisResourceWithStreamingResponse,
    AsyncAnalysisResourceWithStreamingResponse,
)
from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ....types.ai import incubator_validate_params
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.ai.incubator_validate_response import IncubatorValidateResponse
from ....types.ai.incubator_retrieve_pitches_response import IncubatorRetrievePitchesResponse

__all__ = ["IncubatorResource", "AsyncIncubatorResource"]


class IncubatorResource(SyncAPIResource):
    @cached_property
    def pitch(self) -> PitchResource:
        return PitchResource(self._client)

    @cached_property
    def analysis(self) -> AnalysisResource:
        return AnalysisResource(self._client)

    @cached_property
    def with_raw_response(self) -> IncubatorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return IncubatorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IncubatorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return IncubatorResourceWithStreamingResponse(self)

    def retrieve_pitches(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IncubatorRetrievePitchesResponse:
        """List All User Business Pitches"""
        return self._get(
            "/ai/incubator/pitches",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IncubatorRetrievePitchesResponse,
        )

    def validate(
        self,
        *,
        concept: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IncubatorValidateResponse:
        """
        Rapid Idea Validation Engine

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/incubator/validate",
            body=maybe_transform({"concept": concept}, incubator_validate_params.IncubatorValidateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IncubatorValidateResponse,
        )


class AsyncIncubatorResource(AsyncAPIResource):
    @cached_property
    def pitch(self) -> AsyncPitchResource:
        return AsyncPitchResource(self._client)

    @cached_property
    def analysis(self) -> AsyncAnalysisResource:
        return AsyncAnalysisResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncIncubatorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncIncubatorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIncubatorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncIncubatorResourceWithStreamingResponse(self)

    async def retrieve_pitches(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IncubatorRetrievePitchesResponse:
        """List All User Business Pitches"""
        return await self._get(
            "/ai/incubator/pitches",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IncubatorRetrievePitchesResponse,
        )

    async def validate(
        self,
        *,
        concept: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> IncubatorValidateResponse:
        """
        Rapid Idea Validation Engine

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/incubator/validate",
            body=await async_maybe_transform({"concept": concept}, incubator_validate_params.IncubatorValidateParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=IncubatorValidateResponse,
        )


class IncubatorResourceWithRawResponse:
    def __init__(self, incubator: IncubatorResource) -> None:
        self._incubator = incubator

        self.retrieve_pitches = to_raw_response_wrapper(
            incubator.retrieve_pitches,
        )
        self.validate = to_raw_response_wrapper(
            incubator.validate,
        )

    @cached_property
    def pitch(self) -> PitchResourceWithRawResponse:
        return PitchResourceWithRawResponse(self._incubator.pitch)

    @cached_property
    def analysis(self) -> AnalysisResourceWithRawResponse:
        return AnalysisResourceWithRawResponse(self._incubator.analysis)


class AsyncIncubatorResourceWithRawResponse:
    def __init__(self, incubator: AsyncIncubatorResource) -> None:
        self._incubator = incubator

        self.retrieve_pitches = async_to_raw_response_wrapper(
            incubator.retrieve_pitches,
        )
        self.validate = async_to_raw_response_wrapper(
            incubator.validate,
        )

    @cached_property
    def pitch(self) -> AsyncPitchResourceWithRawResponse:
        return AsyncPitchResourceWithRawResponse(self._incubator.pitch)

    @cached_property
    def analysis(self) -> AsyncAnalysisResourceWithRawResponse:
        return AsyncAnalysisResourceWithRawResponse(self._incubator.analysis)


class IncubatorResourceWithStreamingResponse:
    def __init__(self, incubator: IncubatorResource) -> None:
        self._incubator = incubator

        self.retrieve_pitches = to_streamed_response_wrapper(
            incubator.retrieve_pitches,
        )
        self.validate = to_streamed_response_wrapper(
            incubator.validate,
        )

    @cached_property
    def pitch(self) -> PitchResourceWithStreamingResponse:
        return PitchResourceWithStreamingResponse(self._incubator.pitch)

    @cached_property
    def analysis(self) -> AnalysisResourceWithStreamingResponse:
        return AnalysisResourceWithStreamingResponse(self._incubator.analysis)


class AsyncIncubatorResourceWithStreamingResponse:
    def __init__(self, incubator: AsyncIncubatorResource) -> None:
        self._incubator = incubator

        self.retrieve_pitches = async_to_streamed_response_wrapper(
            incubator.retrieve_pitches,
        )
        self.validate = async_to_streamed_response_wrapper(
            incubator.validate,
        )

    @cached_property
    def pitch(self) -> AsyncPitchResourceWithStreamingResponse:
        return AsyncPitchResourceWithStreamingResponse(self._incubator.pitch)

    @cached_property
    def analysis(self) -> AsyncAnalysisResourceWithStreamingResponse:
        return AsyncAnalysisResourceWithStreamingResponse(self._incubator.analysis)
