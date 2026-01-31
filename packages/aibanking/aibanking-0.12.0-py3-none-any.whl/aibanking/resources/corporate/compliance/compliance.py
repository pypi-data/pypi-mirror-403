# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from datetime import date
from typing_extensions import Literal

import httpx

from .audits import (
    AuditsResource,
    AsyncAuditsResource,
    AuditsResourceWithRawResponse,
    AsyncAuditsResourceWithRawResponse,
    AuditsResourceWithStreamingResponse,
    AsyncAuditsResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ....types.corporate import (
    compliance_screen_pep_params,
    compliance_screen_media_params,
    compliance_screen_sanctions_params,
)
from ....types.corporate.compliance_screen_pep_response import ComplianceScreenPepResponse
from ....types.corporate.compliance_screen_media_response import ComplianceScreenMediaResponse
from ....types.corporate.compliance_screen_sanctions_response import ComplianceScreenSanctionsResponse

__all__ = ["ComplianceResource", "AsyncComplianceResource"]


class ComplianceResource(SyncAPIResource):
    @cached_property
    def audits(self) -> AuditsResource:
        return AuditsResource(self._client)

    @cached_property
    def with_raw_response(self) -> ComplianceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return ComplianceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ComplianceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return ComplianceResourceWithStreamingResponse(self)

    def screen_media(
        self,
        *,
        query: str,
        depth: Literal["shallow", "deep"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenMediaResponse:
        """
        Adverse Media Sentiment Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/compliance/media",
            body=maybe_transform(
                {
                    "query": query,
                    "depth": depth,
                },
                compliance_screen_media_params.ComplianceScreenMediaParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenMediaResponse,
        )

    def screen_pep(
        self,
        *,
        full_name: str,
        dob: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenPepResponse:
        """
        Politically Exposed Person (PEP) Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/compliance/pep",
            body=maybe_transform(
                {
                    "full_name": full_name,
                    "dob": dob,
                },
                compliance_screen_pep_params.ComplianceScreenPepParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenPepResponse,
        )

    def screen_sanctions(
        self,
        *,
        entities: Iterable[compliance_screen_sanctions_params.Entity],
        check_type: Literal["standard", "enhanced_due_diligence"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenSanctionsResponse:
        """
        Enhanced Global Sanctions Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/compliance/sanctions",
            body=maybe_transform(
                {
                    "entities": entities,
                    "check_type": check_type,
                },
                compliance_screen_sanctions_params.ComplianceScreenSanctionsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenSanctionsResponse,
        )


class AsyncComplianceResource(AsyncAPIResource):
    @cached_property
    def audits(self) -> AsyncAuditsResource:
        return AsyncAuditsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncComplianceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncComplianceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncComplianceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncComplianceResourceWithStreamingResponse(self)

    async def screen_media(
        self,
        *,
        query: str,
        depth: Literal["shallow", "deep"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenMediaResponse:
        """
        Adverse Media Sentiment Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/compliance/media",
            body=await async_maybe_transform(
                {
                    "query": query,
                    "depth": depth,
                },
                compliance_screen_media_params.ComplianceScreenMediaParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenMediaResponse,
        )

    async def screen_pep(
        self,
        *,
        full_name: str,
        dob: Union[str, date] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenPepResponse:
        """
        Politically Exposed Person (PEP) Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/compliance/pep",
            body=await async_maybe_transform(
                {
                    "full_name": full_name,
                    "dob": dob,
                },
                compliance_screen_pep_params.ComplianceScreenPepParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenPepResponse,
        )

    async def screen_sanctions(
        self,
        *,
        entities: Iterable[compliance_screen_sanctions_params.Entity],
        check_type: Literal["standard", "enhanced_due_diligence"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> ComplianceScreenSanctionsResponse:
        """
        Enhanced Global Sanctions Screening

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/compliance/sanctions",
            body=await async_maybe_transform(
                {
                    "entities": entities,
                    "check_type": check_type,
                },
                compliance_screen_sanctions_params.ComplianceScreenSanctionsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=ComplianceScreenSanctionsResponse,
        )


class ComplianceResourceWithRawResponse:
    def __init__(self, compliance: ComplianceResource) -> None:
        self._compliance = compliance

        self.screen_media = to_raw_response_wrapper(
            compliance.screen_media,
        )
        self.screen_pep = to_raw_response_wrapper(
            compliance.screen_pep,
        )
        self.screen_sanctions = to_raw_response_wrapper(
            compliance.screen_sanctions,
        )

    @cached_property
    def audits(self) -> AuditsResourceWithRawResponse:
        return AuditsResourceWithRawResponse(self._compliance.audits)


class AsyncComplianceResourceWithRawResponse:
    def __init__(self, compliance: AsyncComplianceResource) -> None:
        self._compliance = compliance

        self.screen_media = async_to_raw_response_wrapper(
            compliance.screen_media,
        )
        self.screen_pep = async_to_raw_response_wrapper(
            compliance.screen_pep,
        )
        self.screen_sanctions = async_to_raw_response_wrapper(
            compliance.screen_sanctions,
        )

    @cached_property
    def audits(self) -> AsyncAuditsResourceWithRawResponse:
        return AsyncAuditsResourceWithRawResponse(self._compliance.audits)


class ComplianceResourceWithStreamingResponse:
    def __init__(self, compliance: ComplianceResource) -> None:
        self._compliance = compliance

        self.screen_media = to_streamed_response_wrapper(
            compliance.screen_media,
        )
        self.screen_pep = to_streamed_response_wrapper(
            compliance.screen_pep,
        )
        self.screen_sanctions = to_streamed_response_wrapper(
            compliance.screen_sanctions,
        )

    @cached_property
    def audits(self) -> AuditsResourceWithStreamingResponse:
        return AuditsResourceWithStreamingResponse(self._compliance.audits)


class AsyncComplianceResourceWithStreamingResponse:
    def __init__(self, compliance: AsyncComplianceResource) -> None:
        self._compliance = compliance

        self.screen_media = async_to_streamed_response_wrapper(
            compliance.screen_media,
        )
        self.screen_pep = async_to_streamed_response_wrapper(
            compliance.screen_pep,
        )
        self.screen_sanctions = async_to_streamed_response_wrapper(
            compliance.screen_sanctions,
        )

    @cached_property
    def audits(self) -> AsyncAuditsResourceWithStreamingResponse:
        return AsyncAuditsResourceWithStreamingResponse(self._compliance.audits)
