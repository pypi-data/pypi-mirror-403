# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.corporate.treasury import cash_flow_forecast_params
from ....types.corporate.treasury.cash_flow_forecast_response import CashFlowForecastResponse

__all__ = ["CashFlowResource", "AsyncCashFlowResource"]


class CashFlowResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> CashFlowResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return CashFlowResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CashFlowResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return CashFlowResourceWithStreamingResponse(self)

    def forecast(
        self,
        *,
        forecast_horizon_days: int | Omit = omit,
        include_scenario_analysis: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CashFlowForecastResponse:
        """
        Retrieves an advanced AI-driven cash flow forecast for the organization,
        projecting liquidity, identifying potential surpluses or deficits, and providing
        recommendations for optimal treasury management.

        Args:
          forecast_horizon_days: The number of days into the future for which to generate the cash flow forecast
              (e.g., 30, 90, 180).

          include_scenario_analysis: If true, the forecast will include best-case and worst-case scenario analysis
              alongside the most likely projection.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/corporate/treasury/cash-flow/forecast",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "forecast_horizon_days": forecast_horizon_days,
                        "include_scenario_analysis": include_scenario_analysis,
                    },
                    cash_flow_forecast_params.CashFlowForecastParams,
                ),
            ),
            cast_to=CashFlowForecastResponse,
        )


class AsyncCashFlowResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncCashFlowResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCashFlowResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCashFlowResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncCashFlowResourceWithStreamingResponse(self)

    async def forecast(
        self,
        *,
        forecast_horizon_days: int | Omit = omit,
        include_scenario_analysis: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> CashFlowForecastResponse:
        """
        Retrieves an advanced AI-driven cash flow forecast for the organization,
        projecting liquidity, identifying potential surpluses or deficits, and providing
        recommendations for optimal treasury management.

        Args:
          forecast_horizon_days: The number of days into the future for which to generate the cash flow forecast
              (e.g., 30, 90, 180).

          include_scenario_analysis: If true, the forecast will include best-case and worst-case scenario analysis
              alongside the most likely projection.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/corporate/treasury/cash-flow/forecast",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "forecast_horizon_days": forecast_horizon_days,
                        "include_scenario_analysis": include_scenario_analysis,
                    },
                    cash_flow_forecast_params.CashFlowForecastParams,
                ),
            ),
            cast_to=CashFlowForecastResponse,
        )


class CashFlowResourceWithRawResponse:
    def __init__(self, cash_flow: CashFlowResource) -> None:
        self._cash_flow = cash_flow

        self.forecast = to_raw_response_wrapper(
            cash_flow.forecast,
        )


class AsyncCashFlowResourceWithRawResponse:
    def __init__(self, cash_flow: AsyncCashFlowResource) -> None:
        self._cash_flow = cash_flow

        self.forecast = async_to_raw_response_wrapper(
            cash_flow.forecast,
        )


class CashFlowResourceWithStreamingResponse:
    def __init__(self, cash_flow: CashFlowResource) -> None:
        self._cash_flow = cash_flow

        self.forecast = to_streamed_response_wrapper(
            cash_flow.forecast,
        )


class AsyncCashFlowResourceWithStreamingResponse:
    def __init__(self, cash_flow: AsyncCashFlowResource) -> None:
        self._cash_flow = cash_flow

        self.forecast = async_to_streamed_response_wrapper(
            cash_flow.forecast,
        )
