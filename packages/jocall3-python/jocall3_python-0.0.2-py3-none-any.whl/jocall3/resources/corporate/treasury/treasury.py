# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from .cash_flow import (
    CashFlowResource,
    AsyncCashFlowResource,
    CashFlowResourceWithRawResponse,
    AsyncCashFlowResourceWithRawResponse,
    CashFlowResourceWithStreamingResponse,
    AsyncCashFlowResourceWithStreamingResponse,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.corporate.treasury_get_liquidity_positions_response import TreasuryGetLiquidityPositionsResponse

__all__ = ["TreasuryResource", "AsyncTreasuryResource"]


class TreasuryResource(SyncAPIResource):
    @cached_property
    def cash_flow(self) -> CashFlowResource:
        return CashFlowResource(self._client)

    @cached_property
    def with_raw_response(self) -> TreasuryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return TreasuryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TreasuryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return TreasuryResourceWithStreamingResponse(self)

    def get_liquidity_positions(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TreasuryGetLiquidityPositionsResponse:
        """
        Provides a real-time overview of the organization's liquidity across all
        accounts, currencies, and short-term investments.
        """
        return self._get(
            "/corporate/treasury/liquidity-positions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TreasuryGetLiquidityPositionsResponse,
        )


class AsyncTreasuryResource(AsyncAPIResource):
    @cached_property
    def cash_flow(self) -> AsyncCashFlowResource:
        return AsyncCashFlowResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncTreasuryResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncTreasuryResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTreasuryResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncTreasuryResourceWithStreamingResponse(self)

    async def get_liquidity_positions(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> TreasuryGetLiquidityPositionsResponse:
        """
        Provides a real-time overview of the organization's liquidity across all
        accounts, currencies, and short-term investments.
        """
        return await self._get(
            "/corporate/treasury/liquidity-positions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TreasuryGetLiquidityPositionsResponse,
        )


class TreasuryResourceWithRawResponse:
    def __init__(self, treasury: TreasuryResource) -> None:
        self._treasury = treasury

        self.get_liquidity_positions = to_raw_response_wrapper(
            treasury.get_liquidity_positions,
        )

    @cached_property
    def cash_flow(self) -> CashFlowResourceWithRawResponse:
        return CashFlowResourceWithRawResponse(self._treasury.cash_flow)


class AsyncTreasuryResourceWithRawResponse:
    def __init__(self, treasury: AsyncTreasuryResource) -> None:
        self._treasury = treasury

        self.get_liquidity_positions = async_to_raw_response_wrapper(
            treasury.get_liquidity_positions,
        )

    @cached_property
    def cash_flow(self) -> AsyncCashFlowResourceWithRawResponse:
        return AsyncCashFlowResourceWithRawResponse(self._treasury.cash_flow)


class TreasuryResourceWithStreamingResponse:
    def __init__(self, treasury: TreasuryResource) -> None:
        self._treasury = treasury

        self.get_liquidity_positions = to_streamed_response_wrapper(
            treasury.get_liquidity_positions,
        )

    @cached_property
    def cash_flow(self) -> CashFlowResourceWithStreamingResponse:
        return CashFlowResourceWithStreamingResponse(self._treasury.cash_flow)


class AsyncTreasuryResourceWithStreamingResponse:
    def __init__(self, treasury: AsyncTreasuryResource) -> None:
        self._treasury = treasury

        self.get_liquidity_positions = async_to_streamed_response_wrapper(
            treasury.get_liquidity_positions,
        )

    @cached_property
    def cash_flow(self) -> AsyncCashFlowResourceWithStreamingResponse:
        return AsyncCashFlowResourceWithStreamingResponse(self._treasury.cash_flow)
