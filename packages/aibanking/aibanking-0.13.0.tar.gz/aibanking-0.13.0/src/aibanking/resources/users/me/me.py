# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .devices import (
    DevicesResource,
    AsyncDevicesResource,
    DevicesResourceWithRawResponse,
    AsyncDevicesResourceWithRawResponse,
    DevicesResourceWithStreamingResponse,
    AsyncDevicesResourceWithStreamingResponse,
)
from .security import (
    SecurityResource,
    AsyncSecurityResource,
    SecurityResourceWithRawResponse,
    AsyncSecurityResourceWithRawResponse,
    SecurityResourceWithStreamingResponse,
    AsyncSecurityResourceWithStreamingResponse,
)
from ...._types import Body, Query, Headers, NoneType, NotGiven, not_given
from ...._compat import cached_property
from .biometrics import (
    BiometricsResource,
    AsyncBiometricsResource,
    BiometricsResourceWithRawResponse,
    AsyncBiometricsResourceWithRawResponse,
    BiometricsResourceWithStreamingResponse,
    AsyncBiometricsResourceWithStreamingResponse,
)
from .preferences import (
    PreferencesResource,
    AsyncPreferencesResource,
    PreferencesResourceWithRawResponse,
    AsyncPreferencesResourceWithRawResponse,
    PreferencesResourceWithStreamingResponse,
    AsyncPreferencesResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.users.me_retrieve_response import MeRetrieveResponse

__all__ = ["MeResource", "AsyncMeResource"]


class MeResource(SyncAPIResource):
    @cached_property
    def preferences(self) -> PreferencesResource:
        return PreferencesResource(self._client)

    @cached_property
    def security(self) -> SecurityResource:
        return SecurityResource(self._client)

    @cached_property
    def devices(self) -> DevicesResource:
        return DevicesResource(self._client)

    @cached_property
    def biometrics(self) -> BiometricsResource:
        return BiometricsResource(self._client)

    @cached_property
    def with_raw_response(self) -> MeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return MeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return MeResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeRetrieveResponse:
        """get Me"""
        return self._get(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeRetrieveResponse,
        )

    def update(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """update Me"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def delete(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """delete Me"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncMeResource(AsyncAPIResource):
    @cached_property
    def preferences(self) -> AsyncPreferencesResource:
        return AsyncPreferencesResource(self._client)

    @cached_property
    def security(self) -> AsyncSecurityResource:
        return AsyncSecurityResource(self._client)

    @cached_property
    def devices(self) -> AsyncDevicesResource:
        return AsyncDevicesResource(self._client)

    @cached_property
    def biometrics(self) -> AsyncBiometricsResource:
        return AsyncBiometricsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncMeResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncMeResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMeResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncMeResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeRetrieveResponse:
        """get Me"""
        return await self._get(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeRetrieveResponse,
        )

    async def update(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """update Me"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def delete(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """delete Me"""
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            "/users/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class MeResourceWithRawResponse:
    def __init__(self, me: MeResource) -> None:
        self._me = me

        self.retrieve = to_raw_response_wrapper(
            me.retrieve,
        )
        self.update = to_raw_response_wrapper(
            me.update,
        )
        self.delete = to_raw_response_wrapper(
            me.delete,
        )

    @cached_property
    def preferences(self) -> PreferencesResourceWithRawResponse:
        return PreferencesResourceWithRawResponse(self._me.preferences)

    @cached_property
    def security(self) -> SecurityResourceWithRawResponse:
        return SecurityResourceWithRawResponse(self._me.security)

    @cached_property
    def devices(self) -> DevicesResourceWithRawResponse:
        return DevicesResourceWithRawResponse(self._me.devices)

    @cached_property
    def biometrics(self) -> BiometricsResourceWithRawResponse:
        return BiometricsResourceWithRawResponse(self._me.biometrics)


class AsyncMeResourceWithRawResponse:
    def __init__(self, me: AsyncMeResource) -> None:
        self._me = me

        self.retrieve = async_to_raw_response_wrapper(
            me.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            me.update,
        )
        self.delete = async_to_raw_response_wrapper(
            me.delete,
        )

    @cached_property
    def preferences(self) -> AsyncPreferencesResourceWithRawResponse:
        return AsyncPreferencesResourceWithRawResponse(self._me.preferences)

    @cached_property
    def security(self) -> AsyncSecurityResourceWithRawResponse:
        return AsyncSecurityResourceWithRawResponse(self._me.security)

    @cached_property
    def devices(self) -> AsyncDevicesResourceWithRawResponse:
        return AsyncDevicesResourceWithRawResponse(self._me.devices)

    @cached_property
    def biometrics(self) -> AsyncBiometricsResourceWithRawResponse:
        return AsyncBiometricsResourceWithRawResponse(self._me.biometrics)


class MeResourceWithStreamingResponse:
    def __init__(self, me: MeResource) -> None:
        self._me = me

        self.retrieve = to_streamed_response_wrapper(
            me.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            me.update,
        )
        self.delete = to_streamed_response_wrapper(
            me.delete,
        )

    @cached_property
    def preferences(self) -> PreferencesResourceWithStreamingResponse:
        return PreferencesResourceWithStreamingResponse(self._me.preferences)

    @cached_property
    def security(self) -> SecurityResourceWithStreamingResponse:
        return SecurityResourceWithStreamingResponse(self._me.security)

    @cached_property
    def devices(self) -> DevicesResourceWithStreamingResponse:
        return DevicesResourceWithStreamingResponse(self._me.devices)

    @cached_property
    def biometrics(self) -> BiometricsResourceWithStreamingResponse:
        return BiometricsResourceWithStreamingResponse(self._me.biometrics)


class AsyncMeResourceWithStreamingResponse:
    def __init__(self, me: AsyncMeResource) -> None:
        self._me = me

        self.retrieve = async_to_streamed_response_wrapper(
            me.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            me.update,
        )
        self.delete = async_to_streamed_response_wrapper(
            me.delete,
        )

    @cached_property
    def preferences(self) -> AsyncPreferencesResourceWithStreamingResponse:
        return AsyncPreferencesResourceWithStreamingResponse(self._me.preferences)

    @cached_property
    def security(self) -> AsyncSecurityResourceWithStreamingResponse:
        return AsyncSecurityResourceWithStreamingResponse(self._me.security)

    @cached_property
    def devices(self) -> AsyncDevicesResourceWithStreamingResponse:
        return AsyncDevicesResourceWithStreamingResponse(self._me.devices)

    @cached_property
    def biometrics(self) -> AsyncBiometricsResourceWithStreamingResponse:
        return AsyncBiometricsResourceWithStreamingResponse(self._me.biometrics)
