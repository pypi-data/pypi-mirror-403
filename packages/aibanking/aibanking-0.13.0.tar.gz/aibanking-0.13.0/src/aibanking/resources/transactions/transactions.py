# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Iterable
from typing_extensions import Literal

import httpx

from ...types import (
    transaction_list_params,
    transaction_split_params,
    transaction_add_notes_params,
    transaction_categorize_params,
    transaction_initiate_dispute_params,
)
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from .insights import (
    InsightsResource,
    AsyncInsightsResource,
    InsightsResourceWithRawResponse,
    AsyncInsightsResourceWithRawResponse,
    InsightsResourceWithStreamingResponse,
    AsyncInsightsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from .recurring import (
    RecurringResource,
    AsyncRecurringResource,
    RecurringResourceWithRawResponse,
    AsyncRecurringResourceWithRawResponse,
    RecurringResourceWithStreamingResponse,
    AsyncRecurringResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.transaction_list_response import TransactionListResponse
from ...types.transaction_retrieve_response import TransactionRetrieveResponse
from ...types.transaction_categorize_response import TransactionCategorizeResponse

__all__ = ["TransactionsResource", "AsyncTransactionsResource"]


class TransactionsResource(SyncAPIResource):
    @cached_property
    def recurring(self) -> RecurringResource:
        return RecurringResource(self._client)

    @cached_property
    def insights(self) -> InsightsResource:
        return InsightsResource(self._client)

    @cached_property
    def with_raw_response(self) -> TransactionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return TransactionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TransactionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return TransactionsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        transaction_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionRetrieveResponse:
        """
        Get Transaction Deep Metadata

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return self._get(
            f"/transactions/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionRetrieveResponse,
        )

    def list(
        self,
        *,
        limit: int | Omit = omit,
        max_amount: float | Omit = omit,
        min_amount: float | Omit = omit,
        offset: int | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionListResponse:
        """
        Global Transaction Search & Filter

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "max_amount": max_amount,
                        "min_amount": min_amount,
                        "offset": offset,
                        "type": type,
                    },
                    transaction_list_params.TransactionListParams,
                ),
            ),
            cast_to=TransactionListResponse,
        )

    def add_notes(
        self,
        transaction_id: str,
        *,
        notes: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Attach Manual Notes to Transaction

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/transactions/{transaction_id}/notes",
            body=maybe_transform({"notes": notes}, transaction_add_notes_params.TransactionAddNotesParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def categorize(
        self,
        transaction_id: str,
        *,
        category: str,
        apply_to_future: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionCategorizeResponse:
        """
        Override AI Categorization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return self._put(
            f"/transactions/{transaction_id}/categorize",
            body=maybe_transform(
                {
                    "category": category,
                    "apply_to_future": apply_to_future,
                },
                transaction_categorize_params.TransactionCategorizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionCategorizeResponse,
        )

    def initiate_dispute(
        self,
        transaction_id: str,
        *,
        reason: Literal["fraudulent", "duplicate", "incorrect_amount", "service_not_rendered"],
        evidence_files: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Initiate Transaction Dispute

        Args:
          evidence_files: URIs to evidence

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/transactions/{transaction_id}/dispute",
            body=maybe_transform(
                {
                    "reason": reason,
                    "evidence_files": evidence_files,
                },
                transaction_initiate_dispute_params.TransactionInitiateDisputeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def split(
        self,
        transaction_id: str,
        *,
        splits: Iterable[transaction_split_params.Split],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Split Transaction Across Multiple Categories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/transactions/{transaction_id}/split",
            body=maybe_transform({"splits": splits}, transaction_split_params.TransactionSplitParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class AsyncTransactionsResource(AsyncAPIResource):
    @cached_property
    def recurring(self) -> AsyncRecurringResource:
        return AsyncRecurringResource(self._client)

    @cached_property
    def insights(self) -> AsyncInsightsResource:
        return AsyncInsightsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncTransactionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncTransactionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTransactionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncTransactionsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        transaction_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionRetrieveResponse:
        """
        Get Transaction Deep Metadata

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return await self._get(
            f"/transactions/{transaction_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionRetrieveResponse,
        )

    async def list(
        self,
        *,
        limit: int | Omit = omit,
        max_amount: float | Omit = omit,
        min_amount: float | Omit = omit,
        offset: int | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionListResponse:
        """
        Global Transaction Search & Filter

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "max_amount": max_amount,
                        "min_amount": min_amount,
                        "offset": offset,
                        "type": type,
                    },
                    transaction_list_params.TransactionListParams,
                ),
            ),
            cast_to=TransactionListResponse,
        )

    async def add_notes(
        self,
        transaction_id: str,
        *,
        notes: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Attach Manual Notes to Transaction

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/transactions/{transaction_id}/notes",
            body=await async_maybe_transform({"notes": notes}, transaction_add_notes_params.TransactionAddNotesParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def categorize(
        self,
        transaction_id: str,
        *,
        category: str,
        apply_to_future: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionCategorizeResponse:
        """
        Override AI Categorization

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return await self._put(
            f"/transactions/{transaction_id}/categorize",
            body=await async_maybe_transform(
                {
                    "category": category,
                    "apply_to_future": apply_to_future,
                },
                transaction_categorize_params.TransactionCategorizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionCategorizeResponse,
        )

    async def initiate_dispute(
        self,
        transaction_id: str,
        *,
        reason: Literal["fraudulent", "duplicate", "incorrect_amount", "service_not_rendered"],
        evidence_files: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Initiate Transaction Dispute

        Args:
          evidence_files: URIs to evidence

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/transactions/{transaction_id}/dispute",
            body=await async_maybe_transform(
                {
                    "reason": reason,
                    "evidence_files": evidence_files,
                },
                transaction_initiate_dispute_params.TransactionInitiateDisputeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def split(
        self,
        transaction_id: str,
        *,
        splits: Iterable[transaction_split_params.Split],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Split Transaction Across Multiple Categories

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/transactions/{transaction_id}/split",
            body=await async_maybe_transform({"splits": splits}, transaction_split_params.TransactionSplitParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )


class TransactionsResourceWithRawResponse:
    def __init__(self, transactions: TransactionsResource) -> None:
        self._transactions = transactions

        self.retrieve = to_raw_response_wrapper(
            transactions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            transactions.list,
        )
        self.add_notes = to_raw_response_wrapper(
            transactions.add_notes,
        )
        self.categorize = to_raw_response_wrapper(
            transactions.categorize,
        )
        self.initiate_dispute = to_raw_response_wrapper(
            transactions.initiate_dispute,
        )
        self.split = to_raw_response_wrapper(
            transactions.split,
        )

    @cached_property
    def recurring(self) -> RecurringResourceWithRawResponse:
        return RecurringResourceWithRawResponse(self._transactions.recurring)

    @cached_property
    def insights(self) -> InsightsResourceWithRawResponse:
        return InsightsResourceWithRawResponse(self._transactions.insights)


class AsyncTransactionsResourceWithRawResponse:
    def __init__(self, transactions: AsyncTransactionsResource) -> None:
        self._transactions = transactions

        self.retrieve = async_to_raw_response_wrapper(
            transactions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            transactions.list,
        )
        self.add_notes = async_to_raw_response_wrapper(
            transactions.add_notes,
        )
        self.categorize = async_to_raw_response_wrapper(
            transactions.categorize,
        )
        self.initiate_dispute = async_to_raw_response_wrapper(
            transactions.initiate_dispute,
        )
        self.split = async_to_raw_response_wrapper(
            transactions.split,
        )

    @cached_property
    def recurring(self) -> AsyncRecurringResourceWithRawResponse:
        return AsyncRecurringResourceWithRawResponse(self._transactions.recurring)

    @cached_property
    def insights(self) -> AsyncInsightsResourceWithRawResponse:
        return AsyncInsightsResourceWithRawResponse(self._transactions.insights)


class TransactionsResourceWithStreamingResponse:
    def __init__(self, transactions: TransactionsResource) -> None:
        self._transactions = transactions

        self.retrieve = to_streamed_response_wrapper(
            transactions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            transactions.list,
        )
        self.add_notes = to_streamed_response_wrapper(
            transactions.add_notes,
        )
        self.categorize = to_streamed_response_wrapper(
            transactions.categorize,
        )
        self.initiate_dispute = to_streamed_response_wrapper(
            transactions.initiate_dispute,
        )
        self.split = to_streamed_response_wrapper(
            transactions.split,
        )

    @cached_property
    def recurring(self) -> RecurringResourceWithStreamingResponse:
        return RecurringResourceWithStreamingResponse(self._transactions.recurring)

    @cached_property
    def insights(self) -> InsightsResourceWithStreamingResponse:
        return InsightsResourceWithStreamingResponse(self._transactions.insights)


class AsyncTransactionsResourceWithStreamingResponse:
    def __init__(self, transactions: AsyncTransactionsResource) -> None:
        self._transactions = transactions

        self.retrieve = async_to_streamed_response_wrapper(
            transactions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            transactions.list,
        )
        self.add_notes = async_to_streamed_response_wrapper(
            transactions.add_notes,
        )
        self.categorize = async_to_streamed_response_wrapper(
            transactions.categorize,
        )
        self.initiate_dispute = async_to_streamed_response_wrapper(
            transactions.initiate_dispute,
        )
        self.split = async_to_streamed_response_wrapper(
            transactions.split,
        )

    @cached_property
    def recurring(self) -> AsyncRecurringResourceWithStreamingResponse:
        return AsyncRecurringResourceWithStreamingResponse(self._transactions.recurring)

    @cached_property
    def insights(self) -> AsyncInsightsResourceWithStreamingResponse:
        return AsyncInsightsResourceWithStreamingResponse(self._transactions.insights)
