# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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
from ....types.users.me import security_retrieve_log_params
from ....types.users.me.security_rotate_keys_response import SecurityRotateKeysResponse
from ....types.users.me.security_retrieve_log_response import SecurityRetrieveLogResponse

__all__ = ["SecurityResource", "AsyncSecurityResource"]


class SecurityResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SecurityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SecurityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SecurityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SecurityResourceWithStreamingResponse(self)

    def retrieve_log(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SecurityRetrieveLogResponse:
        """
        Retrieve Security Access Logs

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/users/me/security/log",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    security_retrieve_log_params.SecurityRetrieveLogParams,
                ),
            ),
            cast_to=SecurityRetrieveLogResponse,
        )

    def rotate_keys(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SecurityRotateKeysResponse:
        """Rotate API/Access Keys"""
        return self._post(
            "/users/me/security/rotate-keys",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SecurityRotateKeysResponse,
        )


class AsyncSecurityResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSecurityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSecurityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSecurityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSecurityResourceWithStreamingResponse(self)

    async def retrieve_log(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SecurityRetrieveLogResponse:
        """
        Retrieve Security Access Logs

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/users/me/security/log",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    security_retrieve_log_params.SecurityRetrieveLogParams,
                ),
            ),
            cast_to=SecurityRetrieveLogResponse,
        )

    async def rotate_keys(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SecurityRotateKeysResponse:
        """Rotate API/Access Keys"""
        return await self._post(
            "/users/me/security/rotate-keys",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SecurityRotateKeysResponse,
        )


class SecurityResourceWithRawResponse:
    def __init__(self, security: SecurityResource) -> None:
        self._security = security

        self.retrieve_log = to_raw_response_wrapper(
            security.retrieve_log,
        )
        self.rotate_keys = to_raw_response_wrapper(
            security.rotate_keys,
        )


class AsyncSecurityResourceWithRawResponse:
    def __init__(self, security: AsyncSecurityResource) -> None:
        self._security = security

        self.retrieve_log = async_to_raw_response_wrapper(
            security.retrieve_log,
        )
        self.rotate_keys = async_to_raw_response_wrapper(
            security.rotate_keys,
        )


class SecurityResourceWithStreamingResponse:
    def __init__(self, security: SecurityResource) -> None:
        self._security = security

        self.retrieve_log = to_streamed_response_wrapper(
            security.retrieve_log,
        )
        self.rotate_keys = to_streamed_response_wrapper(
            security.rotate_keys,
        )


class AsyncSecurityResourceWithStreamingResponse:
    def __init__(self, security: AsyncSecurityResource) -> None:
        self._security = security

        self.retrieve_log = async_to_streamed_response_wrapper(
            security.retrieve_log,
        )
        self.rotate_keys = async_to_streamed_response_wrapper(
            security.rotate_keys,
        )
