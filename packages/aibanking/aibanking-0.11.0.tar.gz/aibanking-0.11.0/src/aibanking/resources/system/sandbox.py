# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

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
from ...types.system import sandbox_simulate_error_params
from ...types.system.sandbox_simulate_error_response import SandboxSimulateErrorResponse

__all__ = ["SandboxResource", "AsyncSandboxResource"]


class SandboxResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SandboxResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SandboxResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SandboxResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SandboxResourceWithStreamingResponse(self)

    def reset(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Reset Sandbox Ledger Data"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            "/system/sandbox/reset",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def simulate_error(
        self,
        *,
        error_code: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SandboxSimulateErrorResponse:
        """
        Force Specific API Error (For Testing)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/system/sandbox/simulate-error",
            body=maybe_transform({"error_code": error_code}, sandbox_simulate_error_params.SandboxSimulateErrorParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SandboxSimulateErrorResponse,
        )


class AsyncSandboxResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSandboxResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSandboxResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSandboxResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSandboxResourceWithStreamingResponse(self)

    async def reset(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """Reset Sandbox Ledger Data"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            "/system/sandbox/reset",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def simulate_error(
        self,
        *,
        error_code: int,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SandboxSimulateErrorResponse:
        """
        Force Specific API Error (For Testing)

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/system/sandbox/simulate-error",
            body=await async_maybe_transform(
                {"error_code": error_code}, sandbox_simulate_error_params.SandboxSimulateErrorParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SandboxSimulateErrorResponse,
        )


class SandboxResourceWithRawResponse:
    def __init__(self, sandbox: SandboxResource) -> None:
        self._sandbox = sandbox

        self.reset = to_raw_response_wrapper(
            sandbox.reset,
        )
        self.simulate_error = to_raw_response_wrapper(
            sandbox.simulate_error,
        )


class AsyncSandboxResourceWithRawResponse:
    def __init__(self, sandbox: AsyncSandboxResource) -> None:
        self._sandbox = sandbox

        self.reset = async_to_raw_response_wrapper(
            sandbox.reset,
        )
        self.simulate_error = async_to_raw_response_wrapper(
            sandbox.simulate_error,
        )


class SandboxResourceWithStreamingResponse:
    def __init__(self, sandbox: SandboxResource) -> None:
        self._sandbox = sandbox

        self.reset = to_streamed_response_wrapper(
            sandbox.reset,
        )
        self.simulate_error = to_streamed_response_wrapper(
            sandbox.simulate_error,
        )


class AsyncSandboxResourceWithStreamingResponse:
    def __init__(self, sandbox: AsyncSandboxResource) -> None:
        self._sandbox = sandbox

        self.reset = async_to_streamed_response_wrapper(
            sandbox.reset,
        )
        self.simulate_error = async_to_streamed_response_wrapper(
            sandbox.simulate_error,
        )
