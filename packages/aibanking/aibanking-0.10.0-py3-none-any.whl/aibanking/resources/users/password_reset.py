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

__all__ = ["PasswordResetResource", "AsyncPasswordResetResource"]


class PasswordResetResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PasswordResetResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return PasswordResetResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PasswordResetResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return PasswordResetResourceWithStreamingResponse(self)

    def confirm(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Confirms the password reset using the received verification code and sets a new
        password.
        """
        return self._post(
            "/users/password-reset/confirm",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def initiate(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Starts the password reset flow by sending a verification code or link to the
        user's registered email or phone.
        """
        return self._post(
            "/users/password-reset/initiate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncPasswordResetResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPasswordResetResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncPasswordResetResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPasswordResetResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncPasswordResetResourceWithStreamingResponse(self)

    async def confirm(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Confirms the password reset using the received verification code and sets a new
        password.
        """
        return await self._post(
            "/users/password-reset/confirm",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def initiate(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Starts the password reset flow by sending a verification code or link to the
        user's registered email or phone.
        """
        return await self._post(
            "/users/password-reset/initiate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class PasswordResetResourceWithRawResponse:
    def __init__(self, password_reset: PasswordResetResource) -> None:
        self._password_reset = password_reset

        self.confirm = to_raw_response_wrapper(
            password_reset.confirm,
        )
        self.initiate = to_raw_response_wrapper(
            password_reset.initiate,
        )


class AsyncPasswordResetResourceWithRawResponse:
    def __init__(self, password_reset: AsyncPasswordResetResource) -> None:
        self._password_reset = password_reset

        self.confirm = async_to_raw_response_wrapper(
            password_reset.confirm,
        )
        self.initiate = async_to_raw_response_wrapper(
            password_reset.initiate,
        )


class PasswordResetResourceWithStreamingResponse:
    def __init__(self, password_reset: PasswordResetResource) -> None:
        self._password_reset = password_reset

        self.confirm = to_streamed_response_wrapper(
            password_reset.confirm,
        )
        self.initiate = to_streamed_response_wrapper(
            password_reset.initiate,
        )


class AsyncPasswordResetResourceWithStreamingResponse:
    def __init__(self, password_reset: AsyncPasswordResetResource) -> None:
        self._password_reset = password_reset

        self.confirm = async_to_streamed_response_wrapper(
            password_reset.confirm,
        )
        self.initiate = async_to_streamed_response_wrapper(
            password_reset.initiate,
        )
