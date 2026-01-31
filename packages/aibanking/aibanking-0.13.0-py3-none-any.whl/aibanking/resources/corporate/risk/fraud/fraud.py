# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .rules import (
    RulesResource,
    AsyncRulesResource,
    RulesResourceWithRawResponse,
    AsyncRulesResourceWithRawResponse,
    RulesResourceWithStreamingResponse,
    AsyncRulesResourceWithStreamingResponse,
)
from ....._types import Body, Query, Headers, NotGiven, not_given
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
from .....types.corporate.risk import fraud_analyze_transaction_params
from .....types.corporate.risk.fraud_analyze_transaction_response import FraudAnalyzeTransactionResponse

__all__ = ["FraudResource", "AsyncFraudResource"]


class FraudResource(SyncAPIResource):
    @cached_property
    def rules(self) -> RulesResource:
        return RulesResource(self._client)

    @cached_property
    def with_raw_response(self) -> FraudResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return FraudResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> FraudResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return FraudResourceWithStreamingResponse(self)

    def analyze_transaction(
        self,
        *,
        transaction_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FraudAnalyzeTransactionResponse:
        """
        Real-time Transaction Fraud Analysis

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/risk/fraud/analyze",
            body=maybe_transform(
                {"transaction_id": transaction_id}, fraud_analyze_transaction_params.FraudAnalyzeTransactionParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FraudAnalyzeTransactionResponse,
        )


class AsyncFraudResource(AsyncAPIResource):
    @cached_property
    def rules(self) -> AsyncRulesResource:
        return AsyncRulesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncFraudResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncFraudResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncFraudResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncFraudResourceWithStreamingResponse(self)

    async def analyze_transaction(
        self,
        *,
        transaction_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> FraudAnalyzeTransactionResponse:
        """
        Real-time Transaction Fraud Analysis

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/risk/fraud/analyze",
            body=await async_maybe_transform(
                {"transaction_id": transaction_id}, fraud_analyze_transaction_params.FraudAnalyzeTransactionParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=FraudAnalyzeTransactionResponse,
        )


class FraudResourceWithRawResponse:
    def __init__(self, fraud: FraudResource) -> None:
        self._fraud = fraud

        self.analyze_transaction = to_raw_response_wrapper(
            fraud.analyze_transaction,
        )

    @cached_property
    def rules(self) -> RulesResourceWithRawResponse:
        return RulesResourceWithRawResponse(self._fraud.rules)


class AsyncFraudResourceWithRawResponse:
    def __init__(self, fraud: AsyncFraudResource) -> None:
        self._fraud = fraud

        self.analyze_transaction = async_to_raw_response_wrapper(
            fraud.analyze_transaction,
        )

    @cached_property
    def rules(self) -> AsyncRulesResourceWithRawResponse:
        return AsyncRulesResourceWithRawResponse(self._fraud.rules)


class FraudResourceWithStreamingResponse:
    def __init__(self, fraud: FraudResource) -> None:
        self._fraud = fraud

        self.analyze_transaction = to_streamed_response_wrapper(
            fraud.analyze_transaction,
        )

    @cached_property
    def rules(self) -> RulesResourceWithStreamingResponse:
        return RulesResourceWithStreamingResponse(self._fraud.rules)


class AsyncFraudResourceWithStreamingResponse:
    def __init__(self, fraud: AsyncFraudResource) -> None:
        self._fraud = fraud

        self.analyze_transaction = async_to_streamed_response_wrapper(
            fraud.analyze_transaction,
        )

    @cached_property
    def rules(self) -> AsyncRulesResourceWithStreamingResponse:
        return AsyncRulesResourceWithStreamingResponse(self._fraud.rules)
