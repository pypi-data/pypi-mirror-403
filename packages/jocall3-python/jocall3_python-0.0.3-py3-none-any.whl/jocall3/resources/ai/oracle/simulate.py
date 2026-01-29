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
from ....types.ai.oracle import simulate_run_advanced_simulation_params
from ....types.ai.oracle.simulate_run_standard_simulation_response import SimulateRunStandardSimulationResponse

__all__ = ["SimulateResource", "AsyncSimulateResource"]


class SimulateResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SimulateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return SimulateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SimulateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return SimulateResourceWithStreamingResponse(self)

    def run_advanced_simulation(
        self,
        *,
        global_economic_factors: object | Omit = omit,
        personal_assumptions: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Engages the Quantum Oracle for highly complex, multi-variable simulations,
        allowing precise control over numerous financial parameters, market conditions,
        and personal events to generate deep, predictive insights and sensitivity
        analysis.

        Args:
          global_economic_factors: Optional: Global economic conditions to apply to all scenarios.

          personal_assumptions: Optional: Personal financial assumptions to override defaults.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/oracle/simulate/advanced",
            body=maybe_transform(
                {
                    "global_economic_factors": global_economic_factors,
                    "personal_assumptions": personal_assumptions,
                },
                simulate_run_advanced_simulation_params.SimulateRunAdvancedSimulationParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def run_standard_simulation(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateRunStandardSimulationResponse:
        """
        Submits a hypothetical scenario to the Quantum Oracle AI for standard financial
        impact analysis. The AI simulates the effect on the user's current financial
        state and provides a summary.
        """
        return self._post(
            "/ai/oracle/simulate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateRunStandardSimulationResponse,
        )


class AsyncSimulateResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSimulateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSimulateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSimulateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncSimulateResourceWithStreamingResponse(self)

    async def run_advanced_simulation(
        self,
        *,
        global_economic_factors: object | Omit = omit,
        personal_assumptions: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Engages the Quantum Oracle for highly complex, multi-variable simulations,
        allowing precise control over numerous financial parameters, market conditions,
        and personal events to generate deep, predictive insights and sensitivity
        analysis.

        Args:
          global_economic_factors: Optional: Global economic conditions to apply to all scenarios.

          personal_assumptions: Optional: Personal financial assumptions to override defaults.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/oracle/simulate/advanced",
            body=await async_maybe_transform(
                {
                    "global_economic_factors": global_economic_factors,
                    "personal_assumptions": personal_assumptions,
                },
                simulate_run_advanced_simulation_params.SimulateRunAdvancedSimulationParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def run_standard_simulation(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulateRunStandardSimulationResponse:
        """
        Submits a hypothetical scenario to the Quantum Oracle AI for standard financial
        impact analysis. The AI simulates the effect on the user's current financial
        state and provides a summary.
        """
        return await self._post(
            "/ai/oracle/simulate",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=SimulateRunStandardSimulationResponse,
        )


class SimulateResourceWithRawResponse:
    def __init__(self, simulate: SimulateResource) -> None:
        self._simulate = simulate

        self.run_advanced_simulation = to_raw_response_wrapper(
            simulate.run_advanced_simulation,
        )
        self.run_standard_simulation = to_raw_response_wrapper(
            simulate.run_standard_simulation,
        )


class AsyncSimulateResourceWithRawResponse:
    def __init__(self, simulate: AsyncSimulateResource) -> None:
        self._simulate = simulate

        self.run_advanced_simulation = async_to_raw_response_wrapper(
            simulate.run_advanced_simulation,
        )
        self.run_standard_simulation = async_to_raw_response_wrapper(
            simulate.run_standard_simulation,
        )


class SimulateResourceWithStreamingResponse:
    def __init__(self, simulate: SimulateResource) -> None:
        self._simulate = simulate

        self.run_advanced_simulation = to_streamed_response_wrapper(
            simulate.run_advanced_simulation,
        )
        self.run_standard_simulation = to_streamed_response_wrapper(
            simulate.run_standard_simulation,
        )


class AsyncSimulateResourceWithStreamingResponse:
    def __init__(self, simulate: AsyncSimulateResource) -> None:
        self._simulate = simulate

        self.run_advanced_simulation = async_to_streamed_response_wrapper(
            simulate.run_advanced_simulation,
        )
        self.run_standard_simulation = async_to_streamed_response_wrapper(
            simulate.run_standard_simulation,
        )
