# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ....._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ....._utils import maybe_transform, async_maybe_transform
from ....._compat import cached_property
from ....._resource import SyncAPIResource, AsyncAPIResource
from ....._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ....._base_client import make_request_options
from .....types.corporate.risk.fraud import rule_list_active_params, rule_update_rule_params
from .....types.corporate.risk.fraud.rule_update_rule_response import RuleUpdateRuleResponse

__all__ = ["RulesResource", "AsyncRulesResource"]


class RulesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> RulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return RulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return RulesResourceWithStreamingResponse(self)

    def list_active(
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
    ) -> object:
        """
        Retrieves a list of AI-powered fraud detection rules currently active for the
        organization, including their parameters, thresholds, and associated actions
        (e.g., flag, block, alert).

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/corporate/risk/fraud/rules",
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
                    rule_list_active_params.RuleListActiveParams,
                ),
            ),
            cast_to=object,
        )

    def update_rule(
        self,
        rule_id: str,
        *,
        action: object | Omit = omit,
        criteria: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RuleUpdateRuleResponse:
        """
        Updates an existing custom AI-powered fraud detection rule, modifying its
        criteria, actions, or status.

        Args:
          action: Action to take when a fraud rule is triggered.

          criteria: Criteria that define when a fraud rule should trigger.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rule_id:
            raise ValueError(f"Expected a non-empty value for `rule_id` but received {rule_id!r}")
        return self._put(
            f"/corporate/risk/fraud/rules/{rule_id}",
            body=maybe_transform(
                {
                    "action": action,
                    "criteria": criteria,
                },
                rule_update_rule_params.RuleUpdateRuleParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RuleUpdateRuleResponse,
        )


class AsyncRulesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncRulesResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncRulesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRulesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncRulesResourceWithStreamingResponse(self)

    async def list_active(
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
    ) -> object:
        """
        Retrieves a list of AI-powered fraud detection rules currently active for the
        organization, including their parameters, thresholds, and associated actions
        (e.g., flag, block, alert).

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/corporate/risk/fraud/rules",
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
                    rule_list_active_params.RuleListActiveParams,
                ),
            ),
            cast_to=object,
        )

    async def update_rule(
        self,
        rule_id: str,
        *,
        action: object | Omit = omit,
        criteria: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> RuleUpdateRuleResponse:
        """
        Updates an existing custom AI-powered fraud detection rule, modifying its
        criteria, actions, or status.

        Args:
          action: Action to take when a fraud rule is triggered.

          criteria: Criteria that define when a fraud rule should trigger.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not rule_id:
            raise ValueError(f"Expected a non-empty value for `rule_id` but received {rule_id!r}")
        return await self._put(
            f"/corporate/risk/fraud/rules/{rule_id}",
            body=await async_maybe_transform(
                {
                    "action": action,
                    "criteria": criteria,
                },
                rule_update_rule_params.RuleUpdateRuleParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=RuleUpdateRuleResponse,
        )


class RulesResourceWithRawResponse:
    def __init__(self, rules: RulesResource) -> None:
        self._rules = rules

        self.list_active = to_raw_response_wrapper(
            rules.list_active,
        )
        self.update_rule = to_raw_response_wrapper(
            rules.update_rule,
        )


class AsyncRulesResourceWithRawResponse:
    def __init__(self, rules: AsyncRulesResource) -> None:
        self._rules = rules

        self.list_active = async_to_raw_response_wrapper(
            rules.list_active,
        )
        self.update_rule = async_to_raw_response_wrapper(
            rules.update_rule,
        )


class RulesResourceWithStreamingResponse:
    def __init__(self, rules: RulesResource) -> None:
        self._rules = rules

        self.list_active = to_streamed_response_wrapper(
            rules.list_active,
        )
        self.update_rule = to_streamed_response_wrapper(
            rules.update_rule,
        )


class AsyncRulesResourceWithStreamingResponse:
    def __init__(self, rules: AsyncRulesResource) -> None:
        self._rules = rules

        self.list_active = async_to_streamed_response_wrapper(
            rules.list_active,
        )
        self.update_rule = async_to_streamed_response_wrapper(
            rules.update_rule,
        )
