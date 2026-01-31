# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import system_get_audit_logs_params
from .sandbox import (
    SandboxResource,
    AsyncSandboxResource,
    SandboxResourceWithRawResponse,
    AsyncSandboxResourceWithRawResponse,
    SandboxResourceWithStreamingResponse,
    AsyncSandboxResourceWithStreamingResponse,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from .webhooks import (
    WebhooksResource,
    AsyncWebhooksResource,
    WebhooksResourceWithRawResponse,
    AsyncWebhooksResourceWithRawResponse,
    WebhooksResourceWithStreamingResponse,
    AsyncWebhooksResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .verification import (
    VerificationResource,
    AsyncVerificationResource,
    VerificationResourceWithRawResponse,
    AsyncVerificationResourceWithRawResponse,
    VerificationResourceWithStreamingResponse,
    AsyncVerificationResourceWithStreamingResponse,
)
from .notifications import (
    NotificationsResource,
    AsyncNotificationsResource,
    NotificationsResourceWithRawResponse,
    AsyncNotificationsResourceWithRawResponse,
    NotificationsResourceWithStreamingResponse,
    AsyncNotificationsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from ...types.system_get_status_response import SystemGetStatusResponse
from ...types.system_get_audit_logs_response import SystemGetAuditLogsResponse

__all__ = ["SystemResource", "AsyncSystemResource"]


class SystemResource(SyncAPIResource):
    @cached_property
    def webhooks(self) -> WebhooksResource:
        return WebhooksResource(self._client)

    @cached_property
    def sandbox(self) -> SandboxResource:
        return SandboxResource(self._client)

    @cached_property
    def verification(self) -> VerificationResource:
        return VerificationResource(self._client)

    @cached_property
    def notifications(self) -> NotificationsResource:
        return NotificationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> SystemResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return SystemResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SystemResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return SystemResourceWithStreamingResponse(self)

    def get_audit_logs(
        self,
        *,
        actor_id: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SystemGetAuditLogsResponse:
        """
        Get Immutable System Audit Trail

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/system/audit-logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "actor_id": actor_id,
                        "limit": limit,
                        "offset": offset,
                    },
                    system_get_audit_logs_params.SystemGetAuditLogsParams,
                ),
            ),
            cast_to=SystemGetAuditLogsResponse,
        )

    def get_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SystemGetStatusResponse:
        """Get Global Infrastructure Health"""
        return self._get(
            "/system/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SystemGetStatusResponse,
        )


class AsyncSystemResource(AsyncAPIResource):
    @cached_property
    def webhooks(self) -> AsyncWebhooksResource:
        return AsyncWebhooksResource(self._client)

    @cached_property
    def sandbox(self) -> AsyncSandboxResource:
        return AsyncSandboxResource(self._client)

    @cached_property
    def verification(self) -> AsyncVerificationResource:
        return AsyncVerificationResource(self._client)

    @cached_property
    def notifications(self) -> AsyncNotificationsResource:
        return AsyncNotificationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSystemResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncSystemResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSystemResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncSystemResourceWithStreamingResponse(self)

    async def get_audit_logs(
        self,
        *,
        actor_id: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SystemGetAuditLogsResponse:
        """
        Get Immutable System Audit Trail

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/system/audit-logs",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "actor_id": actor_id,
                        "limit": limit,
                        "offset": offset,
                    },
                    system_get_audit_logs_params.SystemGetAuditLogsParams,
                ),
            ),
            cast_to=SystemGetAuditLogsResponse,
        )

    async def get_status(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SystemGetStatusResponse:
        """Get Global Infrastructure Health"""
        return await self._get(
            "/system/status",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SystemGetStatusResponse,
        )


class SystemResourceWithRawResponse:
    def __init__(self, system: SystemResource) -> None:
        self._system = system

        self.get_audit_logs = to_raw_response_wrapper(
            system.get_audit_logs,
        )
        self.get_status = to_raw_response_wrapper(
            system.get_status,
        )

    @cached_property
    def webhooks(self) -> WebhooksResourceWithRawResponse:
        return WebhooksResourceWithRawResponse(self._system.webhooks)

    @cached_property
    def sandbox(self) -> SandboxResourceWithRawResponse:
        return SandboxResourceWithRawResponse(self._system.sandbox)

    @cached_property
    def verification(self) -> VerificationResourceWithRawResponse:
        return VerificationResourceWithRawResponse(self._system.verification)

    @cached_property
    def notifications(self) -> NotificationsResourceWithRawResponse:
        return NotificationsResourceWithRawResponse(self._system.notifications)


class AsyncSystemResourceWithRawResponse:
    def __init__(self, system: AsyncSystemResource) -> None:
        self._system = system

        self.get_audit_logs = async_to_raw_response_wrapper(
            system.get_audit_logs,
        )
        self.get_status = async_to_raw_response_wrapper(
            system.get_status,
        )

    @cached_property
    def webhooks(self) -> AsyncWebhooksResourceWithRawResponse:
        return AsyncWebhooksResourceWithRawResponse(self._system.webhooks)

    @cached_property
    def sandbox(self) -> AsyncSandboxResourceWithRawResponse:
        return AsyncSandboxResourceWithRawResponse(self._system.sandbox)

    @cached_property
    def verification(self) -> AsyncVerificationResourceWithRawResponse:
        return AsyncVerificationResourceWithRawResponse(self._system.verification)

    @cached_property
    def notifications(self) -> AsyncNotificationsResourceWithRawResponse:
        return AsyncNotificationsResourceWithRawResponse(self._system.notifications)


class SystemResourceWithStreamingResponse:
    def __init__(self, system: SystemResource) -> None:
        self._system = system

        self.get_audit_logs = to_streamed_response_wrapper(
            system.get_audit_logs,
        )
        self.get_status = to_streamed_response_wrapper(
            system.get_status,
        )

    @cached_property
    def webhooks(self) -> WebhooksResourceWithStreamingResponse:
        return WebhooksResourceWithStreamingResponse(self._system.webhooks)

    @cached_property
    def sandbox(self) -> SandboxResourceWithStreamingResponse:
        return SandboxResourceWithStreamingResponse(self._system.sandbox)

    @cached_property
    def verification(self) -> VerificationResourceWithStreamingResponse:
        return VerificationResourceWithStreamingResponse(self._system.verification)

    @cached_property
    def notifications(self) -> NotificationsResourceWithStreamingResponse:
        return NotificationsResourceWithStreamingResponse(self._system.notifications)


class AsyncSystemResourceWithStreamingResponse:
    def __init__(self, system: AsyncSystemResource) -> None:
        self._system = system

        self.get_audit_logs = async_to_streamed_response_wrapper(
            system.get_audit_logs,
        )
        self.get_status = async_to_streamed_response_wrapper(
            system.get_status,
        )

    @cached_property
    def webhooks(self) -> AsyncWebhooksResourceWithStreamingResponse:
        return AsyncWebhooksResourceWithStreamingResponse(self._system.webhooks)

    @cached_property
    def sandbox(self) -> AsyncSandboxResourceWithStreamingResponse:
        return AsyncSandboxResourceWithStreamingResponse(self._system.sandbox)

    @cached_property
    def verification(self) -> AsyncVerificationResourceWithStreamingResponse:
        return AsyncVerificationResourceWithStreamingResponse(self._system.verification)

    @cached_property
    def notifications(self) -> AsyncNotificationsResourceWithStreamingResponse:
        return AsyncNotificationsResourceWithStreamingResponse(self._system.notifications)
