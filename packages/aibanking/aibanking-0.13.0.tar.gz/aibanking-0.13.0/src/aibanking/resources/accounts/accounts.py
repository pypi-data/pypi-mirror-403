# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ...types import account_link_params, account_open_params, account_retrieve_balance_history_params
from ..._types import Body, Omit, Query, Headers, NoneType, NotGiven, SequenceNotStr, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .statements import (
    StatementsResource,
    AsyncStatementsResource,
    StatementsResourceWithRawResponse,
    AsyncStatementsResourceWithRawResponse,
    StatementsResourceWithStreamingResponse,
    AsyncStatementsResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .transactions import (
    TransactionsResource,
    AsyncTransactionsResource,
    TransactionsResourceWithRawResponse,
    AsyncTransactionsResourceWithRawResponse,
    TransactionsResourceWithStreamingResponse,
    AsyncTransactionsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options
from .overdraft_settings import (
    OverdraftSettingsResource,
    AsyncOverdraftSettingsResource,
    OverdraftSettingsResourceWithRawResponse,
    AsyncOverdraftSettingsResourceWithRawResponse,
    OverdraftSettingsResourceWithStreamingResponse,
    AsyncOverdraftSettingsResourceWithStreamingResponse,
)
from ...types.account_link_response import AccountLinkResponse
from ...types.account_open_response import AccountOpenResponse
from ...types.account_retrieve_me_response import AccountRetrieveMeResponse
from ...types.account_retrieve_details_response import AccountRetrieveDetailsResponse
from ...types.account_retrieve_balance_history_response import AccountRetrieveBalanceHistoryResponse

__all__ = ["AccountsResource", "AsyncAccountsResource"]


class AccountsResource(SyncAPIResource):
    @cached_property
    def transactions(self) -> TransactionsResource:
        return TransactionsResource(self._client)

    @cached_property
    def statements(self) -> StatementsResource:
        return StatementsResource(self._client)

    @cached_property
    def overdraft_settings(self) -> OverdraftSettingsResource:
        return OverdraftSettingsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AccountsResourceWithStreamingResponse(self)

    def delete(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Close Financial Account

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return self._delete(
            f"/accounts/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    def link(
        self,
        *,
        institution_id: str,
        public_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountLinkResponse:
        """
        Link an External Financial Institution

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/accounts/link",
            body=maybe_transform(
                {
                    "institution_id": institution_id,
                    "public_token": public_token,
                },
                account_link_params.AccountLinkParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountLinkResponse,
        )

    def open(
        self,
        *,
        currency: str,
        initial_deposit: float,
        product_type: Literal["quantum_checking", "elite_savings", "high_yield_vault"],
        owners: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountOpenResponse:
        """
        Open a New Quantum Internal Account

        Args:
          owners: User IDs for joint accounts

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/accounts/open",
            body=maybe_transform(
                {
                    "currency": currency,
                    "initial_deposit": initial_deposit,
                    "product_type": product_type,
                    "owners": owners,
                },
                account_open_params.AccountOpenParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountOpenResponse,
        )

    def retrieve_balance_history(
        self,
        account_id: str,
        *,
        period: Literal["1d", "7d", "30d", "1y", "all"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveBalanceHistoryResponse:
        """
        Get Historical Balance Snapshots

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/accounts/{account_id}/balance-history",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {"period": period}, account_retrieve_balance_history_params.AccountRetrieveBalanceHistoryParams
                ),
            ),
            cast_to=AccountRetrieveBalanceHistoryResponse,
        )

    def retrieve_details(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveDetailsResponse:
        """
        get Account Details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/accounts/{account_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountRetrieveDetailsResponse,
        )

    def retrieve_me(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveMeResponse:
        """list Accounts"""
        return self._get(
            "/accounts/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountRetrieveMeResponse,
        )


class AsyncAccountsResource(AsyncAPIResource):
    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        return AsyncTransactionsResource(self._client)

    @cached_property
    def statements(self) -> AsyncStatementsResource:
        return AsyncStatementsResource(self._client)

    @cached_property
    def overdraft_settings(self) -> AsyncOverdraftSettingsResource:
        return AsyncOverdraftSettingsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAccountsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/aibank#accessing-raw-response-data-eg-headers
        """
        return AsyncAccountsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAccountsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/aibank#with_streaming_response
        """
        return AsyncAccountsResourceWithStreamingResponse(self)

    async def delete(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> None:
        """
        Close Financial Account

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        extra_headers = {"Accept": "*/*", **(extra_headers or {})}
        return await self._delete(
            f"/accounts/{account_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=NoneType,
        )

    async def link(
        self,
        *,
        institution_id: str,
        public_token: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountLinkResponse:
        """
        Link an External Financial Institution

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/accounts/link",
            body=await async_maybe_transform(
                {
                    "institution_id": institution_id,
                    "public_token": public_token,
                },
                account_link_params.AccountLinkParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountLinkResponse,
        )

    async def open(
        self,
        *,
        currency: str,
        initial_deposit: float,
        product_type: Literal["quantum_checking", "elite_savings", "high_yield_vault"],
        owners: SequenceNotStr[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountOpenResponse:
        """
        Open a New Quantum Internal Account

        Args:
          owners: User IDs for joint accounts

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/accounts/open",
            body=await async_maybe_transform(
                {
                    "currency": currency,
                    "initial_deposit": initial_deposit,
                    "product_type": product_type,
                    "owners": owners,
                },
                account_open_params.AccountOpenParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountOpenResponse,
        )

    async def retrieve_balance_history(
        self,
        account_id: str,
        *,
        period: Literal["1d", "7d", "30d", "1y", "all"] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveBalanceHistoryResponse:
        """
        Get Historical Balance Snapshots

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/accounts/{account_id}/balance-history",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {"period": period}, account_retrieve_balance_history_params.AccountRetrieveBalanceHistoryParams
                ),
            ),
            cast_to=AccountRetrieveBalanceHistoryResponse,
        )

    async def retrieve_details(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveDetailsResponse:
        """
        get Account Details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/accounts/{account_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountRetrieveDetailsResponse,
        )

    async def retrieve_me(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> AccountRetrieveMeResponse:
        """list Accounts"""
        return await self._get(
            "/accounts/me",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=AccountRetrieveMeResponse,
        )


class AccountsResourceWithRawResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.delete = to_raw_response_wrapper(
            accounts.delete,
        )
        self.link = to_raw_response_wrapper(
            accounts.link,
        )
        self.open = to_raw_response_wrapper(
            accounts.open,
        )
        self.retrieve_balance_history = to_raw_response_wrapper(
            accounts.retrieve_balance_history,
        )
        self.retrieve_details = to_raw_response_wrapper(
            accounts.retrieve_details,
        )
        self.retrieve_me = to_raw_response_wrapper(
            accounts.retrieve_me,
        )

    @cached_property
    def transactions(self) -> TransactionsResourceWithRawResponse:
        return TransactionsResourceWithRawResponse(self._accounts.transactions)

    @cached_property
    def statements(self) -> StatementsResourceWithRawResponse:
        return StatementsResourceWithRawResponse(self._accounts.statements)

    @cached_property
    def overdraft_settings(self) -> OverdraftSettingsResourceWithRawResponse:
        return OverdraftSettingsResourceWithRawResponse(self._accounts.overdraft_settings)


class AsyncAccountsResourceWithRawResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.delete = async_to_raw_response_wrapper(
            accounts.delete,
        )
        self.link = async_to_raw_response_wrapper(
            accounts.link,
        )
        self.open = async_to_raw_response_wrapper(
            accounts.open,
        )
        self.retrieve_balance_history = async_to_raw_response_wrapper(
            accounts.retrieve_balance_history,
        )
        self.retrieve_details = async_to_raw_response_wrapper(
            accounts.retrieve_details,
        )
        self.retrieve_me = async_to_raw_response_wrapper(
            accounts.retrieve_me,
        )

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithRawResponse:
        return AsyncTransactionsResourceWithRawResponse(self._accounts.transactions)

    @cached_property
    def statements(self) -> AsyncStatementsResourceWithRawResponse:
        return AsyncStatementsResourceWithRawResponse(self._accounts.statements)

    @cached_property
    def overdraft_settings(self) -> AsyncOverdraftSettingsResourceWithRawResponse:
        return AsyncOverdraftSettingsResourceWithRawResponse(self._accounts.overdraft_settings)


class AccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AccountsResource) -> None:
        self._accounts = accounts

        self.delete = to_streamed_response_wrapper(
            accounts.delete,
        )
        self.link = to_streamed_response_wrapper(
            accounts.link,
        )
        self.open = to_streamed_response_wrapper(
            accounts.open,
        )
        self.retrieve_balance_history = to_streamed_response_wrapper(
            accounts.retrieve_balance_history,
        )
        self.retrieve_details = to_streamed_response_wrapper(
            accounts.retrieve_details,
        )
        self.retrieve_me = to_streamed_response_wrapper(
            accounts.retrieve_me,
        )

    @cached_property
    def transactions(self) -> TransactionsResourceWithStreamingResponse:
        return TransactionsResourceWithStreamingResponse(self._accounts.transactions)

    @cached_property
    def statements(self) -> StatementsResourceWithStreamingResponse:
        return StatementsResourceWithStreamingResponse(self._accounts.statements)

    @cached_property
    def overdraft_settings(self) -> OverdraftSettingsResourceWithStreamingResponse:
        return OverdraftSettingsResourceWithStreamingResponse(self._accounts.overdraft_settings)


class AsyncAccountsResourceWithStreamingResponse:
    def __init__(self, accounts: AsyncAccountsResource) -> None:
        self._accounts = accounts

        self.delete = async_to_streamed_response_wrapper(
            accounts.delete,
        )
        self.link = async_to_streamed_response_wrapper(
            accounts.link,
        )
        self.open = async_to_streamed_response_wrapper(
            accounts.open,
        )
        self.retrieve_balance_history = async_to_streamed_response_wrapper(
            accounts.retrieve_balance_history,
        )
        self.retrieve_details = async_to_streamed_response_wrapper(
            accounts.retrieve_details,
        )
        self.retrieve_me = async_to_streamed_response_wrapper(
            accounts.retrieve_me,
        )

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithStreamingResponse:
        return AsyncTransactionsResourceWithStreamingResponse(self._accounts.transactions)

    @cached_property
    def statements(self) -> AsyncStatementsResourceWithStreamingResponse:
        return AsyncStatementsResourceWithStreamingResponse(self._accounts.statements)

    @cached_property
    def overdraft_settings(self) -> AsyncOverdraftSettingsResourceWithStreamingResponse:
        return AsyncOverdraftSettingsResourceWithStreamingResponse(self._accounts.overdraft_settings)
