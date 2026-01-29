# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Query, Headers, NotGiven, not_given
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .investments import (
    InvestmentsResource,
    AsyncInvestmentsResource,
    InvestmentsResourceWithRawResponse,
    AsyncInvestmentsResourceWithRawResponse,
    InvestmentsResourceWithStreamingResponse,
    AsyncInvestmentsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options

__all__ = ["SustainabilityResource", "AsyncSustainabilityResource"]


class SustainabilityResource(SyncAPIResource):
    @cached_property
    def investments(self) -> InvestmentsResource:
        return InvestmentsResource(self._client)

    @cached_property
    def with_raw_response(self) -> SustainabilityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return SustainabilityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> SustainabilityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return SustainabilityResourceWithStreamingResponse(self)

    def retrieve_carbon_footprint(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Generates a detailed report of the user's estimated carbon footprint based on
        transaction data, lifestyle choices, and AI-driven impact assessments, offering
        insights and reduction strategies.
        """
        return self._get(
            "/sustainability/carbon-footprint",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncSustainabilityResource(AsyncAPIResource):
    @cached_property
    def investments(self) -> AsyncInvestmentsResource:
        return AsyncInvestmentsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncSustainabilityResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncSustainabilityResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncSustainabilityResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncSustainabilityResourceWithStreamingResponse(self)

    async def retrieve_carbon_footprint(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Generates a detailed report of the user's estimated carbon footprint based on
        transaction data, lifestyle choices, and AI-driven impact assessments, offering
        insights and reduction strategies.
        """
        return await self._get(
            "/sustainability/carbon-footprint",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class SustainabilityResourceWithRawResponse:
    def __init__(self, sustainability: SustainabilityResource) -> None:
        self._sustainability = sustainability

        self.retrieve_carbon_footprint = to_raw_response_wrapper(
            sustainability.retrieve_carbon_footprint,
        )

    @cached_property
    def investments(self) -> InvestmentsResourceWithRawResponse:
        return InvestmentsResourceWithRawResponse(self._sustainability.investments)


class AsyncSustainabilityResourceWithRawResponse:
    def __init__(self, sustainability: AsyncSustainabilityResource) -> None:
        self._sustainability = sustainability

        self.retrieve_carbon_footprint = async_to_raw_response_wrapper(
            sustainability.retrieve_carbon_footprint,
        )

    @cached_property
    def investments(self) -> AsyncInvestmentsResourceWithRawResponse:
        return AsyncInvestmentsResourceWithRawResponse(self._sustainability.investments)


class SustainabilityResourceWithStreamingResponse:
    def __init__(self, sustainability: SustainabilityResource) -> None:
        self._sustainability = sustainability

        self.retrieve_carbon_footprint = to_streamed_response_wrapper(
            sustainability.retrieve_carbon_footprint,
        )

    @cached_property
    def investments(self) -> InvestmentsResourceWithStreamingResponse:
        return InvestmentsResourceWithStreamingResponse(self._sustainability.investments)


class AsyncSustainabilityResourceWithStreamingResponse:
    def __init__(self, sustainability: AsyncSustainabilityResource) -> None:
        self._sustainability = sustainability

        self.retrieve_carbon_footprint = async_to_streamed_response_wrapper(
            sustainability.retrieve_carbon_footprint,
        )

    @cached_property
    def investments(self) -> AsyncInvestmentsResourceWithStreamingResponse:
        return AsyncInvestmentsResourceWithStreamingResponse(self._sustainability.investments)
