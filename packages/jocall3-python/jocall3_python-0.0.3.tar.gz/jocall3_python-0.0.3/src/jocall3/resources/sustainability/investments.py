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
from ..._base_client import make_request_options
from ...types.sustainability.investment_analyze_impact_response import InvestmentAnalyzeImpactResponse

__all__ = ["InvestmentsResource", "AsyncInvestmentsResource"]


class InvestmentsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> InvestmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return InvestmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> InvestmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return InvestmentsResourceWithStreamingResponse(self)

    def analyze_impact(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InvestmentAnalyzeImpactResponse:
        """
        Provides an AI-driven analysis of the Environmental, Social, and Governance
        (ESG) impact of the user's entire investment portfolio, benchmarking against
        industry standards and suggesting more sustainable alternatives.

              example:
                code: UNAUTHENTICATED
                message: 'Authentication failed: Invalid or missing access token.'
                timestamp: '2024-07-22T08:00:00Z'

        '403': description: >-
        """
        return self._get(
            "/sustainability/investments/impact",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvestmentAnalyzeImpactResponse,
        )


class AsyncInvestmentsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncInvestmentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncInvestmentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncInvestmentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncInvestmentsResourceWithStreamingResponse(self)

    async def analyze_impact(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> InvestmentAnalyzeImpactResponse:
        """
        Provides an AI-driven analysis of the Environmental, Social, and Governance
        (ESG) impact of the user's entire investment portfolio, benchmarking against
        industry standards and suggesting more sustainable alternatives.

              example:
                code: UNAUTHENTICATED
                message: 'Authentication failed: Invalid or missing access token.'
                timestamp: '2024-07-22T08:00:00Z'

        '403': description: >-
        """
        return await self._get(
            "/sustainability/investments/impact",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=InvestmentAnalyzeImpactResponse,
        )


class InvestmentsResourceWithRawResponse:
    def __init__(self, investments: InvestmentsResource) -> None:
        self._investments = investments

        self.analyze_impact = to_raw_response_wrapper(
            investments.analyze_impact,
        )


class AsyncInvestmentsResourceWithRawResponse:
    def __init__(self, investments: AsyncInvestmentsResource) -> None:
        self._investments = investments

        self.analyze_impact = async_to_raw_response_wrapper(
            investments.analyze_impact,
        )


class InvestmentsResourceWithStreamingResponse:
    def __init__(self, investments: InvestmentsResource) -> None:
        self._investments = investments

        self.analyze_impact = to_streamed_response_wrapper(
            investments.analyze_impact,
        )


class AsyncInvestmentsResourceWithStreamingResponse:
    def __init__(self, investments: AsyncInvestmentsResource) -> None:
        self._investments = investments

        self.analyze_impact = async_to_streamed_response_wrapper(
            investments.analyze_impact,
        )
