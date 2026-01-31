# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .prompts import (
    PromptsResource,
    AsyncPromptsResource,
    PromptsResourceWithRawResponse,
    AsyncPromptsResourceWithRawResponse,
    PromptsResourceWithStreamingResponse,
    AsyncPromptsResourceWithStreamingResponse,
)
from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.ai.agent_retrieve_capabilities_response import AgentRetrieveCapabilitiesResponse

__all__ = ["AgentResource", "AsyncAgentResource"]


class AgentResource(SyncAPIResource):
    @cached_property
    def prompts(self) -> PromptsResource:
        return PromptsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AgentResourceWithStreamingResponse(self)

    def retrieve_capabilities(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentRetrieveCapabilitiesResponse:
        """List Quantum Agent Capabilities"""
        return self._get(
            "/ai/agent/capabilities",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentRetrieveCapabilitiesResponse,
        )


class AsyncAgentResource(AsyncAPIResource):
    @cached_property
    def prompts(self) -> AsyncPromptsResource:
        return AsyncPromptsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAgentResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncAgentResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAgentResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncAgentResourceWithStreamingResponse(self)

    async def retrieve_capabilities(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AgentRetrieveCapabilitiesResponse:
        """List Quantum Agent Capabilities"""
        return await self._get(
            "/ai/agent/capabilities",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AgentRetrieveCapabilitiesResponse,
        )


class AgentResourceWithRawResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.retrieve_capabilities = to_raw_response_wrapper(
            agent.retrieve_capabilities,
        )

    @cached_property
    def prompts(self) -> PromptsResourceWithRawResponse:
        return PromptsResourceWithRawResponse(self._agent.prompts)


class AsyncAgentResourceWithRawResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.retrieve_capabilities = async_to_raw_response_wrapper(
            agent.retrieve_capabilities,
        )

    @cached_property
    def prompts(self) -> AsyncPromptsResourceWithRawResponse:
        return AsyncPromptsResourceWithRawResponse(self._agent.prompts)


class AgentResourceWithStreamingResponse:
    def __init__(self, agent: AgentResource) -> None:
        self._agent = agent

        self.retrieve_capabilities = to_streamed_response_wrapper(
            agent.retrieve_capabilities,
        )

    @cached_property
    def prompts(self) -> PromptsResourceWithStreamingResponse:
        return PromptsResourceWithStreamingResponse(self._agent.prompts)


class AsyncAgentResourceWithStreamingResponse:
    def __init__(self, agent: AsyncAgentResource) -> None:
        self._agent = agent

        self.retrieve_capabilities = async_to_streamed_response_wrapper(
            agent.retrieve_capabilities,
        )

    @cached_property
    def prompts(self) -> AsyncPromptsResourceWithStreamingResponse:
        return AsyncPromptsResourceWithStreamingResponse(self._agent.prompts)
