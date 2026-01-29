# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .assets import (
    AssetsResource,
    AsyncAssetsResource,
    AssetsResourceWithRawResponse,
    AsyncAssetsResourceWithRawResponse,
    AssetsResourceWithStreamingResponse,
    AsyncAssetsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from .portfolios import (
    PortfoliosResource,
    AsyncPortfoliosResource,
    PortfoliosResourceWithRawResponse,
    AsyncPortfoliosResourceWithRawResponse,
    PortfoliosResourceWithStreamingResponse,
    AsyncPortfoliosResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["InvestmentsResource", "AsyncInvestmentsResource"]


class InvestmentsResource(SyncAPIResource):
    @cached_property
    def portfolios(self) -> PortfoliosResource:
        return PortfoliosResource(self._client)

    @cached_property
    def assets(self) -> AssetsResource:
        return AssetsResource(self._client)

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


class AsyncInvestmentsResource(AsyncAPIResource):
    @cached_property
    def portfolios(self) -> AsyncPortfoliosResource:
        return AsyncPortfoliosResource(self._client)

    @cached_property
    def assets(self) -> AsyncAssetsResource:
        return AsyncAssetsResource(self._client)

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


class InvestmentsResourceWithRawResponse:
    def __init__(self, investments: InvestmentsResource) -> None:
        self._investments = investments

    @cached_property
    def portfolios(self) -> PortfoliosResourceWithRawResponse:
        return PortfoliosResourceWithRawResponse(self._investments.portfolios)

    @cached_property
    def assets(self) -> AssetsResourceWithRawResponse:
        return AssetsResourceWithRawResponse(self._investments.assets)


class AsyncInvestmentsResourceWithRawResponse:
    def __init__(self, investments: AsyncInvestmentsResource) -> None:
        self._investments = investments

    @cached_property
    def portfolios(self) -> AsyncPortfoliosResourceWithRawResponse:
        return AsyncPortfoliosResourceWithRawResponse(self._investments.portfolios)

    @cached_property
    def assets(self) -> AsyncAssetsResourceWithRawResponse:
        return AsyncAssetsResourceWithRawResponse(self._investments.assets)


class InvestmentsResourceWithStreamingResponse:
    def __init__(self, investments: InvestmentsResource) -> None:
        self._investments = investments

    @cached_property
    def portfolios(self) -> PortfoliosResourceWithStreamingResponse:
        return PortfoliosResourceWithStreamingResponse(self._investments.portfolios)

    @cached_property
    def assets(self) -> AssetsResourceWithStreamingResponse:
        return AssetsResourceWithStreamingResponse(self._investments.assets)


class AsyncInvestmentsResourceWithStreamingResponse:
    def __init__(self, investments: AsyncInvestmentsResource) -> None:
        self._investments = investments

    @cached_property
    def portfolios(self) -> AsyncPortfoliosResourceWithStreamingResponse:
        return AsyncPortfoliosResourceWithStreamingResponse(self._investments.portfolios)

    @cached_property
    def assets(self) -> AsyncAssetsResourceWithStreamingResponse:
        return AsyncAssetsResourceWithStreamingResponse(self._investments.assets)
