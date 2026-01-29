# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .simulate import (
    SimulateResource,
    AsyncSimulateResource,
    SimulateResourceWithRawResponse,
    AsyncSimulateResourceWithRawResponse,
    SimulateResourceWithStreamingResponse,
    AsyncSimulateResourceWithStreamingResponse,
)
from ...._compat import cached_property
from .simulations import (
    SimulationsResource,
    AsyncSimulationsResource,
    SimulationsResourceWithRawResponse,
    AsyncSimulationsResourceWithRawResponse,
    SimulationsResourceWithStreamingResponse,
    AsyncSimulationsResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["OracleResource", "AsyncOracleResource"]


class OracleResource(SyncAPIResource):
    @cached_property
    def simulate(self) -> SimulateResource:
        return SimulateResource(self._client)

    @cached_property
    def simulations(self) -> SimulationsResource:
        return SimulationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> OracleResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return OracleResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OracleResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return OracleResourceWithStreamingResponse(self)


class AsyncOracleResource(AsyncAPIResource):
    @cached_property
    def simulate(self) -> AsyncSimulateResource:
        return AsyncSimulateResource(self._client)

    @cached_property
    def simulations(self) -> AsyncSimulationsResource:
        return AsyncSimulationsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncOracleResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncOracleResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOracleResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncOracleResourceWithStreamingResponse(self)


class OracleResourceWithRawResponse:
    def __init__(self, oracle: OracleResource) -> None:
        self._oracle = oracle

    @cached_property
    def simulate(self) -> SimulateResourceWithRawResponse:
        return SimulateResourceWithRawResponse(self._oracle.simulate)

    @cached_property
    def simulations(self) -> SimulationsResourceWithRawResponse:
        return SimulationsResourceWithRawResponse(self._oracle.simulations)


class AsyncOracleResourceWithRawResponse:
    def __init__(self, oracle: AsyncOracleResource) -> None:
        self._oracle = oracle

    @cached_property
    def simulate(self) -> AsyncSimulateResourceWithRawResponse:
        return AsyncSimulateResourceWithRawResponse(self._oracle.simulate)

    @cached_property
    def simulations(self) -> AsyncSimulationsResourceWithRawResponse:
        return AsyncSimulationsResourceWithRawResponse(self._oracle.simulations)


class OracleResourceWithStreamingResponse:
    def __init__(self, oracle: OracleResource) -> None:
        self._oracle = oracle

    @cached_property
    def simulate(self) -> SimulateResourceWithStreamingResponse:
        return SimulateResourceWithStreamingResponse(self._oracle.simulate)

    @cached_property
    def simulations(self) -> SimulationsResourceWithStreamingResponse:
        return SimulationsResourceWithStreamingResponse(self._oracle.simulations)


class AsyncOracleResourceWithStreamingResponse:
    def __init__(self, oracle: AsyncOracleResource) -> None:
        self._oracle = oracle

    @cached_property
    def simulate(self) -> AsyncSimulateResourceWithStreamingResponse:
        return AsyncSimulateResourceWithStreamingResponse(self._oracle.simulate)

    @cached_property
    def simulations(self) -> AsyncSimulationsResourceWithStreamingResponse:
        return AsyncSimulationsResourceWithStreamingResponse(self._oracle.simulations)
