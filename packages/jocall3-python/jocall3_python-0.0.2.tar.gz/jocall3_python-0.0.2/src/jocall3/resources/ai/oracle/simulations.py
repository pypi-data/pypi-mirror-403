# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Any, cast

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
from ....types.ai.oracle import simulation_list_all_params
from ....types.ai.oracle.simulation_retrieve_results_response import SimulationRetrieveResultsResponse

__all__ = ["SimulationsResource", "AsyncSimulationsResource"]


class SimulationsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> SimulationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return SimulationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SimulationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return SimulationsResourceWithStreamingResponse(self)

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
        Retrieves a list of all financial simulations previously run by the user,
        including their status and summaries.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/ai/oracle/simulations",
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
                    simulation_list_all_params.SimulationListAllParams,
                ),
            ),
            cast_to=object,
        )

    def retrieve_results(
        self,
        simulation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationRetrieveResultsResponse:
        """
        Retrieves the full, detailed results of a specific financial simulation by its
        ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not simulation_id:
            raise ValueError(f"Expected a non-empty value for `simulation_id` but received {simulation_id!r}")
        return cast(
            SimulationRetrieveResultsResponse,
            self._get(
                f"/ai/oracle/simulations/{simulation_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, SimulationRetrieveResultsResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class AsyncSimulationsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncSimulationsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSimulationsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSimulationsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncSimulationsResourceWithStreamingResponse(self)

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
        Retrieves a list of all financial simulations previously run by the user,
        including their status and summaries.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/ai/oracle/simulations",
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
                    simulation_list_all_params.SimulationListAllParams,
                ),
            ),
            cast_to=object,
        )

    async def retrieve_results(
        self,
        simulation_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> SimulationRetrieveResultsResponse:
        """
        Retrieves the full, detailed results of a specific financial simulation by its
        ID.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not simulation_id:
            raise ValueError(f"Expected a non-empty value for `simulation_id` but received {simulation_id!r}")
        return cast(
            SimulationRetrieveResultsResponse,
            await self._get(
                f"/ai/oracle/simulations/{simulation_id}",
                options=make_request_options(
                    extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
                ),
                cast_to=cast(
                    Any, SimulationRetrieveResultsResponse
                ),  # Union types cannot be passed in as arguments in the type system
            ),
        )


class SimulationsResourceWithRawResponse:
    def __init__(self, simulations: SimulationsResource) -> None:
        self._simulations = simulations

        self.list_all = to_raw_response_wrapper(
            simulations.list_all,
        )
        self.retrieve_results = to_raw_response_wrapper(
            simulations.retrieve_results,
        )


class AsyncSimulationsResourceWithRawResponse:
    def __init__(self, simulations: AsyncSimulationsResource) -> None:
        self._simulations = simulations

        self.list_all = async_to_raw_response_wrapper(
            simulations.list_all,
        )
        self.retrieve_results = async_to_raw_response_wrapper(
            simulations.retrieve_results,
        )


class SimulationsResourceWithStreamingResponse:
    def __init__(self, simulations: SimulationsResource) -> None:
        self._simulations = simulations

        self.list_all = to_streamed_response_wrapper(
            simulations.list_all,
        )
        self.retrieve_results = to_streamed_response_wrapper(
            simulations.retrieve_results,
        )


class AsyncSimulationsResourceWithStreamingResponse:
    def __init__(self, simulations: AsyncSimulationsResource) -> None:
        self._simulations = simulations

        self.list_all = async_to_streamed_response_wrapper(
            simulations.list_all,
        )
        self.retrieve_results = async_to_streamed_response_wrapper(
            simulations.retrieve_results,
        )
