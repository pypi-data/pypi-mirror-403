# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.corporate import anomaly_update_status_params
from ...types.corporate.anomaly_list_detected_response import AnomalyListDetectedResponse

__all__ = ["AnomaliesResource", "AsyncAnomaliesResource"]


class AnomaliesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AnomaliesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AnomaliesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AnomaliesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AnomaliesResourceWithStreamingResponse(self)

    def list_detected(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnomalyListDetectedResponse:
        """List detected anomalies"""
        return self._get(
            "/corporate/anomalies",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnomalyListDetectedResponse,
        )

    def update_status(
        self,
        anomaly_id: str,
        *,
        status: Literal["dismissed", "investigating", "resolved"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update anomaly status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not anomaly_id:
            raise ValueError(f"Expected a non-empty value for `anomaly_id` but received {anomaly_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/corporate/anomalies/{anomaly_id}/status",
            body=maybe_transform({"status": status}, anomaly_update_status_params.AnomalyUpdateStatusParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncAnomaliesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncAnomaliesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncAnomaliesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAnomaliesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncAnomaliesResourceWithStreamingResponse(self)

    async def list_detected(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AnomalyListDetectedResponse:
        """List detected anomalies"""
        return await self._get(
            "/corporate/anomalies",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AnomalyListDetectedResponse,
        )

    async def update_status(
        self,
        anomaly_id: str,
        *,
        status: Literal["dismissed", "investigating", "resolved"],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update anomaly status

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not anomaly_id:
            raise ValueError(f"Expected a non-empty value for `anomaly_id` but received {anomaly_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/corporate/anomalies/{anomaly_id}/status",
            body=await async_maybe_transform(
                {"status": status}, anomaly_update_status_params.AnomalyUpdateStatusParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AnomaliesResourceWithRawResponse:
    def __init__(self, anomalies: AnomaliesResource) -> None:
        self._anomalies = anomalies

        self.list_detected = to_raw_response_wrapper(
            anomalies.list_detected,
        )
        self.update_status = to_raw_response_wrapper(
            anomalies.update_status,
        )


class AsyncAnomaliesResourceWithRawResponse:
    def __init__(self, anomalies: AsyncAnomaliesResource) -> None:
        self._anomalies = anomalies

        self.list_detected = async_to_raw_response_wrapper(
            anomalies.list_detected,
        )
        self.update_status = async_to_raw_response_wrapper(
            anomalies.update_status,
        )


class AnomaliesResourceWithStreamingResponse:
    def __init__(self, anomalies: AnomaliesResource) -> None:
        self._anomalies = anomalies

        self.list_detected = to_streamed_response_wrapper(
            anomalies.list_detected,
        )
        self.update_status = to_streamed_response_wrapper(
            anomalies.update_status,
        )


class AsyncAnomaliesResourceWithStreamingResponse:
    def __init__(self, anomalies: AsyncAnomaliesResource) -> None:
        self._anomalies = anomalies

        self.list_detected = async_to_streamed_response_wrapper(
            anomalies.list_detected,
        )
        self.update_status = async_to_streamed_response_wrapper(
            anomalies.update_status,
        )
