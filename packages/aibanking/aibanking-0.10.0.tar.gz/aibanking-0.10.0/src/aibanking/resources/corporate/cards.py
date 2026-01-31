# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ...types.corporate import card_list_all_params, card_get_transactions_params, card_issue_virtual_card_params
from ...types.corporate.card_update_controls_response import CardUpdateControlsResponse
from ...types.corporate.card_toggle_card_lock_response import CardToggleCardLockResponse
from ...types.corporate.card_issue_virtual_card_response import CardIssueVirtualCardResponse

__all__ = ["CardsResource", "AsyncCardsResource"]


class CardsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CardsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return CardsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CardsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return CardsResourceWithStreamingResponse(self)

    def get_transactions(
        self,
        card_id: str,
        *,
        end_date: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        start_date: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a paginated list of transactions made with a specific corporate card,
        including AI categorization and compliance flags.

        Args:
          end_date: End date for filtering results (inclusive, YYYY-MM-DD).

          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          start_date: Start date for filtering results (inclusive, YYYY-MM-DD).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return self._get(
            f"/corporate/cards/{card_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "end_date": end_date,
                        "limit": limit,
                        "offset": offset,
                        "start_date": start_date,
                    },
                    card_get_transactions_params.CardGetTransactionsParams,
                ),
            ),
            cast_to=object,
        )

    def issue_virtual_card(
        self,
        *,
        controls: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardIssueVirtualCardResponse:
        """
        Creates and issues a new virtual corporate card with specified spending limits,
        merchant restrictions, and expiration dates, ideal for secure online purchases
        and temporary projects.

        Args:
          controls: Granular spending controls for a corporate card.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/cards/virtual",
            body=maybe_transform({"controls": controls}, card_issue_virtual_card_params.CardIssueVirtualCardParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardIssueVirtualCardResponse,
        )

    def list_all(
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
        Retrieves a comprehensive list of all physical and virtual corporate cards
        associated with the user's organization, including their status, assigned
        holder, and current spending controls.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/corporate/cards",
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
                    card_list_all_params.CardListAllParams,
                ),
            ),
            cast_to=object,
        )

    def toggle_card_lock(
        self,
        card_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardToggleCardLockResponse:
        """
        Immediately changes the frozen status of a corporate card, preventing or
        allowing transactions in real-time, critical for security and expense
        management.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return self._post(
            f"/corporate/cards/{card_id}/freeze",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardToggleCardLockResponse,
        )

    def update_controls(
        self,
        card_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardUpdateControlsResponse:
        """
        Updates the sophisticated spending controls, limits, and policy overrides for a
        specific corporate card, enabling real-time adjustments for security and budget
        adherence.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return self._put(
            f"/corporate/cards/{card_id}/controls",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardUpdateControlsResponse,
        )


class AsyncCardsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCardsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncCardsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCardsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncCardsResourceWithStreamingResponse(self)

    async def get_transactions(
        self,
        card_id: str,
        *,
        end_date: str | Omit = omit,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        start_date: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a paginated list of transactions made with a specific corporate card,
        including AI categorization and compliance flags.

        Args:
          end_date: End date for filtering results (inclusive, YYYY-MM-DD).

          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          start_date: Start date for filtering results (inclusive, YYYY-MM-DD).

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return await self._get(
            f"/corporate/cards/{card_id}/transactions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "end_date": end_date,
                        "limit": limit,
                        "offset": offset,
                        "start_date": start_date,
                    },
                    card_get_transactions_params.CardGetTransactionsParams,
                ),
            ),
            cast_to=object,
        )

    async def issue_virtual_card(
        self,
        *,
        controls: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardIssueVirtualCardResponse:
        """
        Creates and issues a new virtual corporate card with specified spending limits,
        merchant restrictions, and expiration dates, ideal for secure online purchases
        and temporary projects.

        Args:
          controls: Granular spending controls for a corporate card.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/cards/virtual",
            body=await async_maybe_transform(
                {"controls": controls}, card_issue_virtual_card_params.CardIssueVirtualCardParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardIssueVirtualCardResponse,
        )

    async def list_all(
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
        Retrieves a comprehensive list of all physical and virtual corporate cards
        associated with the user's organization, including their status, assigned
        holder, and current spending controls.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/corporate/cards",
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
                    card_list_all_params.CardListAllParams,
                ),
            ),
            cast_to=object,
        )

    async def toggle_card_lock(
        self,
        card_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardToggleCardLockResponse:
        """
        Immediately changes the frozen status of a corporate card, preventing or
        allowing transactions in real-time, critical for security and expense
        management.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return await self._post(
            f"/corporate/cards/{card_id}/freeze",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardToggleCardLockResponse,
        )

    async def update_controls(
        self,
        card_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardUpdateControlsResponse:
        """
        Updates the sophisticated spending controls, limits, and policy overrides for a
        specific corporate card, enabling real-time adjustments for security and budget
        adherence.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        return await self._put(
            f"/corporate/cards/{card_id}/controls",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardUpdateControlsResponse,
        )


class CardsResourceWithRawResponse:
    def __init__(self, cards: CardsResource) -> None:
        self._cards = cards

        self.get_transactions = to_raw_response_wrapper(
            cards.get_transactions,
        )
        self.issue_virtual_card = to_raw_response_wrapper(
            cards.issue_virtual_card,
        )
        self.list_all = to_raw_response_wrapper(
            cards.list_all,
        )
        self.toggle_card_lock = to_raw_response_wrapper(
            cards.toggle_card_lock,
        )
        self.update_controls = to_raw_response_wrapper(
            cards.update_controls,
        )


class AsyncCardsResourceWithRawResponse:
    def __init__(self, cards: AsyncCardsResource) -> None:
        self._cards = cards

        self.get_transactions = async_to_raw_response_wrapper(
            cards.get_transactions,
        )
        self.issue_virtual_card = async_to_raw_response_wrapper(
            cards.issue_virtual_card,
        )
        self.list_all = async_to_raw_response_wrapper(
            cards.list_all,
        )
        self.toggle_card_lock = async_to_raw_response_wrapper(
            cards.toggle_card_lock,
        )
        self.update_controls = async_to_raw_response_wrapper(
            cards.update_controls,
        )


class CardsResourceWithStreamingResponse:
    def __init__(self, cards: CardsResource) -> None:
        self._cards = cards

        self.get_transactions = to_streamed_response_wrapper(
            cards.get_transactions,
        )
        self.issue_virtual_card = to_streamed_response_wrapper(
            cards.issue_virtual_card,
        )
        self.list_all = to_streamed_response_wrapper(
            cards.list_all,
        )
        self.toggle_card_lock = to_streamed_response_wrapper(
            cards.toggle_card_lock,
        )
        self.update_controls = to_streamed_response_wrapper(
            cards.update_controls,
        )


class AsyncCardsResourceWithStreamingResponse:
    def __init__(self, cards: AsyncCardsResource) -> None:
        self._cards = cards

        self.get_transactions = async_to_streamed_response_wrapper(
            cards.get_transactions,
        )
        self.issue_virtual_card = async_to_streamed_response_wrapper(
            cards.issue_virtual_card,
        )
        self.list_all = async_to_streamed_response_wrapper(
            cards.list_all,
        )
        self.toggle_card_lock = async_to_streamed_response_wrapper(
            cards.toggle_card_lock,
        )
        self.update_controls = async_to_streamed_response_wrapper(
            cards.update_controls,
        )
