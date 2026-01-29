# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from ...._compat import cached_property
from .fraud.fraud import (
    FraudResource,
    AsyncFraudResource,
    FraudResourceWithRawResponse,
    AsyncFraudResourceWithRawResponse,
    FraudResourceWithStreamingResponse,
    AsyncFraudResourceWithStreamingResponse,
)
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["RiskResource", "AsyncRiskResource"]


class RiskResource(SyncAPIResource):
    @cached_property
    def fraud(self) -> FraudResource:
        return FraudResource(self._client)

    @cached_property
    def with_raw_response(self) -> RiskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return RiskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> RiskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return RiskResourceWithStreamingResponse(self)


class AsyncRiskResource(AsyncAPIResource):
    @cached_property
    def fraud(self) -> AsyncFraudResource:
        return AsyncFraudResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncRiskResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncRiskResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncRiskResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncRiskResourceWithStreamingResponse(self)


class RiskResourceWithRawResponse:
    def __init__(self, risk: RiskResource) -> None:
        self._risk = risk

    @cached_property
    def fraud(self) -> FraudResourceWithRawResponse:
        return FraudResourceWithRawResponse(self._risk.fraud)


class AsyncRiskResourceWithRawResponse:
    def __init__(self, risk: AsyncRiskResource) -> None:
        self._risk = risk

    @cached_property
    def fraud(self) -> AsyncFraudResourceWithRawResponse:
        return AsyncFraudResourceWithRawResponse(self._risk.fraud)


class RiskResourceWithStreamingResponse:
    def __init__(self, risk: RiskResource) -> None:
        self._risk = risk

    @cached_property
    def fraud(self) -> FraudResourceWithStreamingResponse:
        return FraudResourceWithStreamingResponse(self._risk.fraud)


class AsyncRiskResourceWithStreamingResponse:
    def __init__(self, risk: AsyncRiskResource) -> None:
        self._risk = risk

    @cached_property
    def fraud(self) -> AsyncFraudResourceWithStreamingResponse:
        return AsyncFraudResourceWithStreamingResponse(self._risk.fraud)
