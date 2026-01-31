# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
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
from ...types.corporate import (
    card_list_all_params,
    card_update_controls_params,
    card_toggle_card_lock_params,
    card_issue_virtual_card_params,
    card_request_physical_card_params,
)
from ...types.corporate.card_list_all_response import CardListAllResponse
from ...types.corporate.card_get_transactions_response import CardGetTransactionsResponse
from ...types.corporate.card_issue_virtual_card_response import CardIssueVirtualCardResponse
from ...types.corporate.card_request_physical_card_response import CardRequestPhysicalCardResponse

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
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardGetTransactionsResponse:
        """
        Get card transactions

        Args:
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
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardGetTransactionsResponse,
        )

    def issue_virtual_card(
        self,
        *,
        holder_name: str,
        monthly_limit: float,
        purpose: str,
        metadata: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardIssueVirtualCardResponse:
        """
        Issue Corporate Virtual Card

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/cards/virtual",
            body=maybe_transform(
                {
                    "holder_name": holder_name,
                    "monthly_limit": monthly_limit,
                    "purpose": purpose,
                    "metadata": metadata,
                },
                card_issue_virtual_card_params.CardIssueVirtualCardParams,
            ),
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
    ) -> CardListAllResponse:
        """
        List all corporate cards

        Args:
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
            cast_to=CardListAllResponse,
        )

    def request_physical_card(
        self,
        *,
        holder_name: str,
        shipping_address: card_request_physical_card_params.ShippingAddress,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardRequestPhysicalCardResponse:
        """
        Request Physical Corporate Card

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/cards/physical",
            body=maybe_transform(
                {
                    "holder_name": holder_name,
                    "shipping_address": shipping_address,
                },
                card_request_physical_card_params.CardRequestPhysicalCardParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardRequestPhysicalCardResponse,
        )

    def toggle_card_lock(
        self,
        card_id: str,
        *,
        frozen: bool,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Toggle Card Lock

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._post(
            f"/corporate/cards/{card_id}/freeze",
            body=maybe_transform({"frozen": frozen}, card_toggle_card_lock_params.CardToggleCardLockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def update_controls(
        self,
        card_id: str,
        *,
        allowed_categories: SequenceNotStr[str] | Omit = omit,
        geo_restriction: SequenceNotStr[str] | Omit = omit,
        monthly_limit: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update Spending Limits & MCC Controls

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._put(
            f"/corporate/cards/{card_id}/controls",
            body=maybe_transform(
                {
                    "allowed_categories": allowed_categories,
                    "geo_restriction": geo_restriction,
                    "monthly_limit": monthly_limit,
                },
                card_update_controls_params.CardUpdateControlsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
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
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardGetTransactionsResponse:
        """
        Get card transactions

        Args:
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
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardGetTransactionsResponse,
        )

    async def issue_virtual_card(
        self,
        *,
        holder_name: str,
        monthly_limit: float,
        purpose: str,
        metadata: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardIssueVirtualCardResponse:
        """
        Issue Corporate Virtual Card

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/cards/virtual",
            body=await async_maybe_transform(
                {
                    "holder_name": holder_name,
                    "monthly_limit": monthly_limit,
                    "purpose": purpose,
                    "metadata": metadata,
                },
                card_issue_virtual_card_params.CardIssueVirtualCardParams,
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
    ) -> CardListAllResponse:
        """
        List all corporate cards

        Args:
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
            cast_to=CardListAllResponse,
        )

    async def request_physical_card(
        self,
        *,
        holder_name: str,
        shipping_address: card_request_physical_card_params.ShippingAddress,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CardRequestPhysicalCardResponse:
        """
        Request Physical Corporate Card

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/cards/physical",
            body=await async_maybe_transform(
                {
                    "holder_name": holder_name,
                    "shipping_address": shipping_address,
                },
                card_request_physical_card_params.CardRequestPhysicalCardParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=CardRequestPhysicalCardResponse,
        )

    async def toggle_card_lock(
        self,
        card_id: str,
        *,
        frozen: bool,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Toggle Card Lock

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._post(
            f"/corporate/cards/{card_id}/freeze",
            body=await async_maybe_transform({"frozen": frozen}, card_toggle_card_lock_params.CardToggleCardLockParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def update_controls(
        self,
        card_id: str,
        *,
        allowed_categories: SequenceNotStr[str] | Omit = omit,
        geo_restriction: SequenceNotStr[str] | Omit = omit,
        monthly_limit: float | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Update Spending Limits & MCC Controls

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not card_id:
            raise ValueError(f"Expected a non-empty value for `card_id` but received {card_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._put(
            f"/corporate/cards/{card_id}/controls",
            body=await async_maybe_transform(
                {
                    "allowed_categories": allowed_categories,
                    "geo_restriction": geo_restriction,
                    "monthly_limit": monthly_limit,
                },
                card_update_controls_params.CardUpdateControlsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
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
        self.request_physical_card = to_raw_response_wrapper(
            cards.request_physical_card,
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
        self.request_physical_card = async_to_raw_response_wrapper(
            cards.request_physical_card,
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
        self.request_physical_card = to_streamed_response_wrapper(
            cards.request_physical_card,
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
        self.request_physical_card = async_to_streamed_response_wrapper(
            cards.request_physical_card,
        )
        self.toggle_card_lock = async_to_streamed_response_wrapper(
            cards.toggle_card_lock,
        )
        self.update_controls = async_to_streamed_response_wrapper(
            cards.update_controls,
        )
