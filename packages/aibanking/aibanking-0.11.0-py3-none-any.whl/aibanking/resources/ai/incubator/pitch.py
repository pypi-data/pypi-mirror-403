# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable

import httpx

from ...._types import Body, Query, Headers, NoneType, NotGiven, not_given
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
from ....types.ai.incubator import pitch_create_params, pitch_update_feedback_params
from ....types.ai.incubator.pitch_create_response import PitchCreateResponse
from ....types.ai.incubator.pitch_retrieve_details_response import PitchRetrieveDetailsResponse

__all__ = ["PitchResource", "AsyncPitchResource"]


class PitchResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PitchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return PitchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PitchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return PitchResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        business_plan: str,
        financial_projections: object,
        founding_team: Iterable[object],
        market_opportunity: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchCreateResponse:
        """
        Submit a High-Potential Business Plan

        Args:
          business_plan: Full text of the concept

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/incubator/pitch",
            body=maybe_transform(
                {
                    "business_plan": business_plan,
                    "financial_projections": financial_projections,
                    "founding_team": founding_team,
                    "market_opportunity": market_opportunity,
                },
                pitch_create_params.PitchCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchCreateResponse,
        )

    def retrieve_details(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchRetrieveDetailsResponse:
        """
        Get Full Pitch AI Deep Dive

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return self._get(
            f"/ai/incubator/pitch/{pitch_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchRetrieveDetailsResponse,
        )

    def update_feedback(
        self,
        pitch_id: str,
        *,
        answers: Iterable[object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Submit Answers to AI Follow-up Questions

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/ai/incubator/pitch/{pitch_id}/feedback",
            body=maybe_transform({"answers": answers}, pitch_update_feedback_params.PitchUpdateFeedbackParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncPitchResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPitchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncPitchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPitchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncPitchResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        business_plan: str,
        financial_projections: object,
        founding_team: Iterable[object],
        market_opportunity: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchCreateResponse:
        """
        Submit a High-Potential Business Plan

        Args:
          business_plan: Full text of the concept

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/incubator/pitch",
            body=await async_maybe_transform(
                {
                    "business_plan": business_plan,
                    "financial_projections": financial_projections,
                    "founding_team": founding_team,
                    "market_opportunity": market_opportunity,
                },
                pitch_create_params.PitchCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchCreateResponse,
        )

    async def retrieve_details(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchRetrieveDetailsResponse:
        """
        Get Full Pitch AI Deep Dive

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return await self._get(
            f"/ai/incubator/pitch/{pitch_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchRetrieveDetailsResponse,
        )

    async def update_feedback(
        self,
        pitch_id: str,
        *,
        answers: Iterable[object],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Submit Answers to AI Follow-up Questions

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/ai/incubator/pitch/{pitch_id}/feedback",
            body=await async_maybe_transform(
                {"answers": answers}, pitch_update_feedback_params.PitchUpdateFeedbackParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class PitchResourceWithRawResponse:
    def __init__(self, pitch: PitchResource) -> None:
        self._pitch = pitch

        self.create = to_raw_response_wrapper(
            pitch.create,
        )
        self.retrieve_details = to_raw_response_wrapper(
            pitch.retrieve_details,
        )
        self.update_feedback = to_raw_response_wrapper(
            pitch.update_feedback,
        )


class AsyncPitchResourceWithRawResponse:
    def __init__(self, pitch: AsyncPitchResource) -> None:
        self._pitch = pitch

        self.create = async_to_raw_response_wrapper(
            pitch.create,
        )
        self.retrieve_details = async_to_raw_response_wrapper(
            pitch.retrieve_details,
        )
        self.update_feedback = async_to_raw_response_wrapper(
            pitch.update_feedback,
        )


class PitchResourceWithStreamingResponse:
    def __init__(self, pitch: PitchResource) -> None:
        self._pitch = pitch

        self.create = to_streamed_response_wrapper(
            pitch.create,
        )
        self.retrieve_details = to_streamed_response_wrapper(
            pitch.retrieve_details,
        )
        self.update_feedback = to_streamed_response_wrapper(
            pitch.update_feedback,
        )


class AsyncPitchResourceWithStreamingResponse:
    def __init__(self, pitch: AsyncPitchResource) -> None:
        self._pitch = pitch

        self.create = async_to_streamed_response_wrapper(
            pitch.create,
        )
        self.retrieve_details = async_to_streamed_response_wrapper(
            pitch.retrieve_details,
        )
        self.update_feedback = async_to_streamed_response_wrapper(
            pitch.update_feedback,
        )
