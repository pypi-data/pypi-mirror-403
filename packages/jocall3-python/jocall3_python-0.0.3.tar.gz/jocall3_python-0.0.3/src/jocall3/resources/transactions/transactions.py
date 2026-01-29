# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import (
    transaction_list_params,
    transaction_categorize_params,
    transaction_update_notes_params,
    transaction_list_recurring_params,
)
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
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
from ...types.transaction_update_notes_response import TransactionUpdateNotesResponse
from ...types.transaction_list_recurring_response import TransactionListRecurringResponse

__all__ = ["TransactionsResource", "AsyncTransactionsResource"]


class TransactionsResource(SyncAPIResource):
    @cached_property
    def insights(self) -> InsightsResource:
        return InsightsResource(self._client)

    @cached_property
    def with_raw_response(self) -> TransactionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return TransactionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TransactionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
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
        Retrieves granular information for a single transaction by its unique ID,
        including AI categorization confidence, merchant details, and associated carbon
        footprint.

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
        category: str | Omit = omit,
        end_date: str | Omit = omit,
        limit: int | Omit = omit,
        max_amount: int | Omit = omit,
        min_amount: int | Omit = omit,
        offset: int | Omit = omit,
        search_query: str | Omit = omit,
        start_date: str | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionListResponse:
        """
        Retrieves a paginated list of the user's transactions, with extensive options
        for filtering by type, category, date range, amount, and intelligent AI-driven
        sorting and search capabilities.

        Args:
          category: Filter transactions by their AI-assigned or user-defined category.

          end_date: Retrieve transactions up to this date (inclusive).

          limit: Maximum number of items to return in a single page.

          max_amount: Filter for transactions with an amount less than or equal to this value.

          min_amount: Filter for transactions with an amount greater than or equal to this value.

          offset: Number of items to skip before starting to collect the result set.

          search_query: Free-text search across transaction descriptions, merchants, and notes.

          start_date: Retrieve transactions from this date (inclusive).

          type: Filter transactions by type (e.g., income, expense, transfer).

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
                        "category": category,
                        "end_date": end_date,
                        "limit": limit,
                        "max_amount": max_amount,
                        "min_amount": min_amount,
                        "offset": offset,
                        "search_query": search_query,
                        "start_date": start_date,
                        "type": type,
                    },
                    transaction_list_params.TransactionListParams,
                ),
            ),
            cast_to=TransactionListResponse,
        )

    def categorize(
        self,
        transaction_id: str,
        *,
        category: str,
        apply_to_future: bool | Omit = omit,
        notes: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionCategorizeResponse:
        """
        Allows the user to override or refine the AI's categorization for a transaction,
        improving future AI accuracy and personal financial reporting.

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
                    "notes": notes,
                },
                transaction_categorize_params.TransactionCategorizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionCategorizeResponse,
        )

    def list_recurring(
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
    ) -> TransactionListRecurringResponse:
        """
        Retrieves a list of all detected or user-defined recurring transactions, useful
        for budget tracking and subscription management.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/transactions/recurring",
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
                    transaction_list_recurring_params.TransactionListRecurringParams,
                ),
            ),
            cast_to=TransactionListRecurringResponse,
        )

    def update_notes(
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
    ) -> TransactionUpdateNotesResponse:
        """
        Allows the user to add or update personal notes for a specific transaction.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return self._put(
            f"/transactions/{transaction_id}/notes",
            body=maybe_transform({"notes": notes}, transaction_update_notes_params.TransactionUpdateNotesParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionUpdateNotesResponse,
        )


class AsyncTransactionsResource(AsyncAPIResource):
    @cached_property
    def insights(self) -> AsyncInsightsResource:
        return AsyncInsightsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncTransactionsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTransactionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTransactionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
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
        Retrieves granular information for a single transaction by its unique ID,
        including AI categorization confidence, merchant details, and associated carbon
        footprint.

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
        category: str | Omit = omit,
        end_date: str | Omit = omit,
        limit: int | Omit = omit,
        max_amount: int | Omit = omit,
        min_amount: int | Omit = omit,
        offset: int | Omit = omit,
        search_query: str | Omit = omit,
        start_date: str | Omit = omit,
        type: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionListResponse:
        """
        Retrieves a paginated list of the user's transactions, with extensive options
        for filtering by type, category, date range, amount, and intelligent AI-driven
        sorting and search capabilities.

        Args:
          category: Filter transactions by their AI-assigned or user-defined category.

          end_date: Retrieve transactions up to this date (inclusive).

          limit: Maximum number of items to return in a single page.

          max_amount: Filter for transactions with an amount less than or equal to this value.

          min_amount: Filter for transactions with an amount greater than or equal to this value.

          offset: Number of items to skip before starting to collect the result set.

          search_query: Free-text search across transaction descriptions, merchants, and notes.

          start_date: Retrieve transactions from this date (inclusive).

          type: Filter transactions by type (e.g., income, expense, transfer).

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
                        "category": category,
                        "end_date": end_date,
                        "limit": limit,
                        "max_amount": max_amount,
                        "min_amount": min_amount,
                        "offset": offset,
                        "search_query": search_query,
                        "start_date": start_date,
                        "type": type,
                    },
                    transaction_list_params.TransactionListParams,
                ),
            ),
            cast_to=TransactionListResponse,
        )

    async def categorize(
        self,
        transaction_id: str,
        *,
        category: str,
        apply_to_future: bool | Omit = omit,
        notes: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TransactionCategorizeResponse:
        """
        Allows the user to override or refine the AI's categorization for a transaction,
        improving future AI accuracy and personal financial reporting.

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
                    "notes": notes,
                },
                transaction_categorize_params.TransactionCategorizeParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionCategorizeResponse,
        )

    async def list_recurring(
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
    ) -> TransactionListRecurringResponse:
        """
        Retrieves a list of all detected or user-defined recurring transactions, useful
        for budget tracking and subscription management.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/transactions/recurring",
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
                    transaction_list_recurring_params.TransactionListRecurringParams,
                ),
            ),
            cast_to=TransactionListRecurringResponse,
        )

    async def update_notes(
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
    ) -> TransactionUpdateNotesResponse:
        """
        Allows the user to add or update personal notes for a specific transaction.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not transaction_id:
            raise ValueError(f"Expected a non-empty value for `transaction_id` but received {transaction_id!r}")
        return await self._put(
            f"/transactions/{transaction_id}/notes",
            body=await async_maybe_transform(
                {"notes": notes}, transaction_update_notes_params.TransactionUpdateNotesParams
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TransactionUpdateNotesResponse,
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
        self.categorize = to_raw_response_wrapper(
            transactions.categorize,
        )
        self.list_recurring = to_raw_response_wrapper(
            transactions.list_recurring,
        )
        self.update_notes = to_raw_response_wrapper(
            transactions.update_notes,
        )

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
        self.categorize = async_to_raw_response_wrapper(
            transactions.categorize,
        )
        self.list_recurring = async_to_raw_response_wrapper(
            transactions.list_recurring,
        )
        self.update_notes = async_to_raw_response_wrapper(
            transactions.update_notes,
        )

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
        self.categorize = to_streamed_response_wrapper(
            transactions.categorize,
        )
        self.list_recurring = to_streamed_response_wrapper(
            transactions.list_recurring,
        )
        self.update_notes = to_streamed_response_wrapper(
            transactions.update_notes,
        )

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
        self.categorize = async_to_streamed_response_wrapper(
            transactions.categorize,
        )
        self.list_recurring = async_to_streamed_response_wrapper(
            transactions.list_recurring,
        )
        self.update_notes = async_to_streamed_response_wrapper(
            transactions.update_notes,
        )

    @cached_property
    def insights(self) -> AsyncInsightsResourceWithStreamingResponse:
        return AsyncInsightsResourceWithStreamingResponse(self._transactions.insights)
