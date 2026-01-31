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
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
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
from ....types.users import me_update_params
from ...._base_client import make_request_options
from ....types.users.me_update_response import MeUpdateResponse
from ....types.users.me_retrieve_response import MeRetrieveResponse

__all__ = ["MeResource", "AsyncMeResource"]


class MeResource(SyncAPIResource):
    @cached_property
    def preferences(self) -> PreferencesResource:
        return PreferencesResource(self._client)

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
        """
        Fetches the complete and dynamically updated profile information for the
        currently authenticated user, encompassing personal details, security status,
        gamification level, loyalty points, and linked identity attributes.
        """
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
        address: object | Omit = omit,
        preferences: me_update_params.Preferences | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeUpdateResponse:
        """
        Updates selected fields of the currently authenticated user's profile
        information.

        Args:
          preferences: User's personalized preferences for the platform.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._put(
            "/users/me",
            body=maybe_transform(
                {
                    "address": address,
                    "preferences": preferences,
                },
                me_update_params.MeUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeUpdateResponse,
        )


class AsyncMeResource(AsyncAPIResource):
    @cached_property
    def preferences(self) -> AsyncPreferencesResource:
        return AsyncPreferencesResource(self._client)

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
        """
        Fetches the complete and dynamically updated profile information for the
        currently authenticated user, encompassing personal details, security status,
        gamification level, loyalty points, and linked identity attributes.
        """
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
        address: object | Omit = omit,
        preferences: me_update_params.Preferences | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> MeUpdateResponse:
        """
        Updates selected fields of the currently authenticated user's profile
        information.

        Args:
          preferences: User's personalized preferences for the platform.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._put(
            "/users/me",
            body=await async_maybe_transform(
                {
                    "address": address,
                    "preferences": preferences,
                },
                me_update_params.MeUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=MeUpdateResponse,
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

    @cached_property
    def preferences(self) -> PreferencesResourceWithRawResponse:
        return PreferencesResourceWithRawResponse(self._me.preferences)

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

    @cached_property
    def preferences(self) -> AsyncPreferencesResourceWithRawResponse:
        return AsyncPreferencesResourceWithRawResponse(self._me.preferences)

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

    @cached_property
    def preferences(self) -> PreferencesResourceWithStreamingResponse:
        return PreferencesResourceWithStreamingResponse(self._me.preferences)

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

    @cached_property
    def preferences(self) -> AsyncPreferencesResourceWithStreamingResponse:
        return AsyncPreferencesResourceWithStreamingResponse(self._me.preferences)

    @cached_property
    def devices(self) -> AsyncDevicesResourceWithStreamingResponse:
        return AsyncDevicesResourceWithStreamingResponse(self._me.devices)

    @cached_property
    def biometrics(self) -> AsyncBiometricsResourceWithStreamingResponse:
        return AsyncBiometricsResourceWithStreamingResponse(self._me.biometrics)
