# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ...types.lending import application_submit_params
from ...types.lending.application_submit_response import ApplicationSubmitResponse
from ...types.lending.application_track_status_response import ApplicationTrackStatusResponse

__all__ = ["ApplicationsResource", "AsyncApplicationsResource"]


class ApplicationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> ApplicationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return ApplicationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ApplicationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return ApplicationsResourceWithStreamingResponse(self)

    def submit(
        self,
        *,
        amount: float,
        employment_data: application_submit_params.EmploymentData,
        loan_type: Literal["MORTGAGE", "PERSONAL", "AUTO", "BUSINESS_EXPANSION"],
        term_months: int,
        assets: Iterable[object] | Omit = omit,
        collateral_id: str | Omit = omit,
        liabilities: Iterable[object] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ApplicationSubmitResponse:
        """
        Submit Advanced Credit Application

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/lending/applications",
            body=maybe_transform(
                {
                    "amount": amount,
                    "employment_data": employment_data,
                    "loan_type": loan_type,
                    "term_months": term_months,
                    "assets": assets,
                    "collateral_id": collateral_id,
                    "liabilities": liabilities,
                },
                application_submit_params.ApplicationSubmitParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ApplicationSubmitResponse,
        )

    def track_status(
        self,
        app_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ApplicationTrackStatusResponse:
        """
        Track Loan Processing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not app_id:
            raise ValueError(f"Expected a non-empty value for `app_id` but received {app_id!r}")
        return self._get(
            f"/lending/applications/{app_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ApplicationTrackStatusResponse,
        )


class AsyncApplicationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncApplicationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncApplicationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncApplicationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncApplicationsResourceWithStreamingResponse(self)

    async def submit(
        self,
        *,
        amount: float,
        employment_data: application_submit_params.EmploymentData,
        loan_type: Literal["MORTGAGE", "PERSONAL", "AUTO", "BUSINESS_EXPANSION"],
        term_months: int,
        assets: Iterable[object] | Omit = omit,
        collateral_id: str | Omit = omit,
        liabilities: Iterable[object] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ApplicationSubmitResponse:
        """
        Submit Advanced Credit Application

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/lending/applications",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "employment_data": employment_data,
                    "loan_type": loan_type,
                    "term_months": term_months,
                    "assets": assets,
                    "collateral_id": collateral_id,
                    "liabilities": liabilities,
                },
                application_submit_params.ApplicationSubmitParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ApplicationSubmitResponse,
        )

    async def track_status(
        self,
        app_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ApplicationTrackStatusResponse:
        """
        Track Loan Processing

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not app_id:
            raise ValueError(f"Expected a non-empty value for `app_id` but received {app_id!r}")
        return await self._get(
            f"/lending/applications/{app_id}/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ApplicationTrackStatusResponse,
        )


class ApplicationsResourceWithRawResponse:
    def __init__(self, applications: ApplicationsResource) -> None:
        self._applications = applications

        self.submit = to_raw_response_wrapper(
            applications.submit,
        )
        self.track_status = to_raw_response_wrapper(
            applications.track_status,
        )


class AsyncApplicationsResourceWithRawResponse:
    def __init__(self, applications: AsyncApplicationsResource) -> None:
        self._applications = applications

        self.submit = async_to_raw_response_wrapper(
            applications.submit,
        )
        self.track_status = async_to_raw_response_wrapper(
            applications.track_status,
        )


class ApplicationsResourceWithStreamingResponse:
    def __init__(self, applications: ApplicationsResource) -> None:
        self._applications = applications

        self.submit = to_streamed_response_wrapper(
            applications.submit,
        )
        self.track_status = to_streamed_response_wrapper(
            applications.track_status,
        )


class AsyncApplicationsResourceWithStreamingResponse:
    def __init__(self, applications: AsyncApplicationsResource) -> None:
        self._applications = applications

        self.submit = async_to_streamed_response_wrapper(
            applications.submit,
        )
        self.track_status = async_to_streamed_response_wrapper(
            applications.track_status,
        )
