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
from ...types.investments import portfolio_list_params

__all__ = ["PortfoliosResource", "AsyncPortfoliosResource"]


class PortfoliosResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PortfoliosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return PortfoliosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PortfoliosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return PortfoliosResourceWithStreamingResponse(self)

    def retrieve(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves detailed information for a specific investment portfolio, including
        holdings, performance, and AI insights.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return self._get(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def update(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Updates high-level details of an investment portfolio, such as name or risk
        tolerance.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return self._put(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def list(
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
        Retrieves a summary of all investment portfolios linked to the user's account.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/investments/portfolios",
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
                    portfolio_list_params.PortfolioListParams,
                ),
            ),
            cast_to=object,
        )

    def rebalance(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Triggers an AI-driven rebalancing process for a specific investment portfolio
        based on a target risk tolerance or strategy.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return self._post(
            f"/investments/portfolios/{portfolio_id}/rebalance",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncPortfoliosResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPortfoliosResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPortfoliosResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPortfoliosResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncPortfoliosResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves detailed information for a specific investment portfolio, including
        holdings, performance, and AI insights.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return await self._get(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def update(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Updates high-level details of an investment portfolio, such as name or risk
        tolerance.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return await self._put(
            f"/investments/portfolios/{portfolio_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def list(
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
        Retrieves a summary of all investment portfolios linked to the user's account.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/investments/portfolios",
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
                    portfolio_list_params.PortfolioListParams,
                ),
            ),
            cast_to=object,
        )

    async def rebalance(
        self,
        portfolio_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Triggers an AI-driven rebalancing process for a specific investment portfolio
        based on a target risk tolerance or strategy.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not portfolio_id:
            raise ValueError(f"Expected a non-empty value for `portfolio_id` but received {portfolio_id!r}")
        return await self._post(
            f"/investments/portfolios/{portfolio_id}/rebalance",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class PortfoliosResourceWithRawResponse:
    def __init__(self, portfolios: PortfoliosResource) -> None:
        self._portfolios = portfolios

        self.retrieve = to_raw_response_wrapper(
            portfolios.retrieve,
        )
        self.update = to_raw_response_wrapper(
            portfolios.update,
        )
        self.list = to_raw_response_wrapper(
            portfolios.list,
        )
        self.rebalance = to_raw_response_wrapper(
            portfolios.rebalance,
        )


class AsyncPortfoliosResourceWithRawResponse:
    def __init__(self, portfolios: AsyncPortfoliosResource) -> None:
        self._portfolios = portfolios

        self.retrieve = async_to_raw_response_wrapper(
            portfolios.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            portfolios.update,
        )
        self.list = async_to_raw_response_wrapper(
            portfolios.list,
        )
        self.rebalance = async_to_raw_response_wrapper(
            portfolios.rebalance,
        )


class PortfoliosResourceWithStreamingResponse:
    def __init__(self, portfolios: PortfoliosResource) -> None:
        self._portfolios = portfolios

        self.retrieve = to_streamed_response_wrapper(
            portfolios.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            portfolios.update,
        )
        self.list = to_streamed_response_wrapper(
            portfolios.list,
        )
        self.rebalance = to_streamed_response_wrapper(
            portfolios.rebalance,
        )


class AsyncPortfoliosResourceWithStreamingResponse:
    def __init__(self, portfolios: AsyncPortfoliosResource) -> None:
        self._portfolios = portfolios

        self.retrieve = async_to_streamed_response_wrapper(
            portfolios.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            portfolios.update,
        )
        self.list = async_to_streamed_response_wrapper(
            portfolios.list,
        )
        self.rebalance = async_to_streamed_response_wrapper(
            portfolios.rebalance,
        )
