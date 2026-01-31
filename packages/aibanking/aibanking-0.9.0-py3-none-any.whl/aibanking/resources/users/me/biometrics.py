# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

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
from ....types.users.me import biometric_enroll_params, biometric_verify_params
from ....types.users.me.biometric_verify_response import BiometricVerifyResponse
from ....types.users.me.biometric_retrieve_status_response import BiometricRetrieveStatusResponse

__all__ = ["BiometricsResource", "AsyncBiometricsResource"]


class BiometricsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> BiometricsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return BiometricsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> BiometricsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return BiometricsResourceWithStreamingResponse(self)

    def enroll(
        self,
        *,
        biometric_type: Literal["fingerprint", "facial_recognition"],
        signature: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Enroll New Biometric Signature

        Args:
          signature: Public key or hash of signature

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/users/me/biometrics/enroll",
            body=maybe_transform(
                {
                    "biometric_type": biometric_type,
                    "signature": signature,
                },
                biometric_enroll_params.BiometricEnrollParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def remove_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Remove All Biometric Data"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            "/users/me/biometrics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def retrieve_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BiometricRetrieveStatusResponse:
        """Get Biometric Enrollment Status"""
        return self._get(
            "/users/me/biometrics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BiometricRetrieveStatusResponse,
        )

    def verify(
        self,
        *,
        biometric_signature: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BiometricVerifyResponse:
        """
        Verify Biometric Data for Sensitive Operations

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/users/me/biometrics/verify",
            body=maybe_transform(
                {"biometric_signature": biometric_signature}, biometric_verify_params.BiometricVerifyParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BiometricVerifyResponse,
        )


class AsyncBiometricsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncBiometricsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncBiometricsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncBiometricsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncBiometricsResourceWithStreamingResponse(self)

    async def enroll(
        self,
        *,
        biometric_type: Literal["fingerprint", "facial_recognition"],
        signature: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Enroll New Biometric Signature

        Args:
          signature: Public key or hash of signature

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/users/me/biometrics/enroll",
            body=await async_maybe_transform(
                {
                    "biometric_type": biometric_type,
                    "signature": signature,
                },
                biometric_enroll_params.BiometricEnrollParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def remove_all(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Remove All Biometric Data"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            "/users/me/biometrics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def retrieve_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BiometricRetrieveStatusResponse:
        """Get Biometric Enrollment Status"""
        return await self._get(
            "/users/me/biometrics",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BiometricRetrieveStatusResponse,
        )

    async def verify(
        self,
        *,
        biometric_signature: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> BiometricVerifyResponse:
        """
        Verify Biometric Data for Sensitive Operations

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/users/me/biometrics/verify",
            body=await async_maybe_transform(
                {"biometric_signature": biometric_signature}, biometric_verify_params.BiometricVerifyParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=BiometricVerifyResponse,
        )


class BiometricsResourceWithRawResponse:
    def __init__(self, biometrics: BiometricsResource) -> None:
        self._biometrics = biometrics

        self.enroll = to_raw_response_wrapper(
            biometrics.enroll,
        )
        self.remove_all = to_raw_response_wrapper(
            biometrics.remove_all,
        )
        self.retrieve_status = to_raw_response_wrapper(
            biometrics.retrieve_status,
        )
        self.verify = to_raw_response_wrapper(
            biometrics.verify,
        )


class AsyncBiometricsResourceWithRawResponse:
    def __init__(self, biometrics: AsyncBiometricsResource) -> None:
        self._biometrics = biometrics

        self.enroll = async_to_raw_response_wrapper(
            biometrics.enroll,
        )
        self.remove_all = async_to_raw_response_wrapper(
            biometrics.remove_all,
        )
        self.retrieve_status = async_to_raw_response_wrapper(
            biometrics.retrieve_status,
        )
        self.verify = async_to_raw_response_wrapper(
            biometrics.verify,
        )


class BiometricsResourceWithStreamingResponse:
    def __init__(self, biometrics: BiometricsResource) -> None:
        self._biometrics = biometrics

        self.enroll = to_streamed_response_wrapper(
            biometrics.enroll,
        )
        self.remove_all = to_streamed_response_wrapper(
            biometrics.remove_all,
        )
        self.retrieve_status = to_streamed_response_wrapper(
            biometrics.retrieve_status,
        )
        self.verify = to_streamed_response_wrapper(
            biometrics.verify,
        )


class AsyncBiometricsResourceWithStreamingResponse:
    def __init__(self, biometrics: AsyncBiometricsResource) -> None:
        self._biometrics = biometrics

        self.enroll = async_to_streamed_response_wrapper(
            biometrics.enroll,
        )
        self.remove_all = async_to_streamed_response_wrapper(
            biometrics.remove_all,
        )
        self.retrieve_status = async_to_streamed_response_wrapper(
            biometrics.retrieve_status,
        )
        self.verify = async_to_streamed_response_wrapper(
            biometrics.verify,
        )
