# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .ads import (
    AdsResource,
    AsyncAdsResource,
    AdsResourceWithRawResponse,
    AsyncAdsResourceWithRawResponse,
    AdsResourceWithStreamingResponse,
    AsyncAdsResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .oracle.oracle import (
    OracleResource,
    AsyncOracleResource,
    OracleResourceWithRawResponse,
    AsyncOracleResourceWithRawResponse,
    OracleResourceWithStreamingResponse,
    AsyncOracleResourceWithStreamingResponse,
)
from .advisor.advisor import (
    AdvisorResource,
    AsyncAdvisorResource,
    AdvisorResourceWithRawResponse,
    AsyncAdvisorResourceWithRawResponse,
    AdvisorResourceWithStreamingResponse,
    AsyncAdvisorResourceWithStreamingResponse,
)
from .incubator.incubator import (
    IncubatorResource,
    AsyncIncubatorResource,
    IncubatorResourceWithRawResponse,
    AsyncIncubatorResourceWithRawResponse,
    IncubatorResourceWithStreamingResponse,
    AsyncIncubatorResourceWithStreamingResponse,
)

__all__ = ["AIResource", "AsyncAIResource"]


class AIResource(SyncAPIResource):
    @cached_property
    def advisor(self) -> AdvisorResource:
        return AdvisorResource(self._client)

    @cached_property
    def oracle(self) -> OracleResource:
        return OracleResource(self._client)

    @cached_property
    def incubator(self) -> IncubatorResource:
        return IncubatorResource(self._client)

    @cached_property
    def ads(self) -> AdsResource:
        return AdsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AIResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AIResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AIResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AIResourceWithStreamingResponse(self)


class AsyncAIResource(AsyncAPIResource):
    @cached_property
    def advisor(self) -> AsyncAdvisorResource:
        return AsyncAdvisorResource(self._client)

    @cached_property
    def oracle(self) -> AsyncOracleResource:
        return AsyncOracleResource(self._client)

    @cached_property
    def incubator(self) -> AsyncIncubatorResource:
        return AsyncIncubatorResource(self._client)

    @cached_property
    def ads(self) -> AsyncAdsResource:
        return AsyncAdsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncAIResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncAIResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncAIResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncAIResourceWithStreamingResponse(self)


class AIResourceWithRawResponse:
    def __init__(self, ai: AIResource) -> None:
        self._ai = ai

    @cached_property
    def advisor(self) -> AdvisorResourceWithRawResponse:
        return AdvisorResourceWithRawResponse(self._ai.advisor)

    @cached_property
    def oracle(self) -> OracleResourceWithRawResponse:
        return OracleResourceWithRawResponse(self._ai.oracle)

    @cached_property
    def incubator(self) -> IncubatorResourceWithRawResponse:
        return IncubatorResourceWithRawResponse(self._ai.incubator)

    @cached_property
    def ads(self) -> AdsResourceWithRawResponse:
        return AdsResourceWithRawResponse(self._ai.ads)


class AsyncAIResourceWithRawResponse:
    def __init__(self, ai: AsyncAIResource) -> None:
        self._ai = ai

    @cached_property
    def advisor(self) -> AsyncAdvisorResourceWithRawResponse:
        return AsyncAdvisorResourceWithRawResponse(self._ai.advisor)

    @cached_property
    def oracle(self) -> AsyncOracleResourceWithRawResponse:
        return AsyncOracleResourceWithRawResponse(self._ai.oracle)

    @cached_property
    def incubator(self) -> AsyncIncubatorResourceWithRawResponse:
        return AsyncIncubatorResourceWithRawResponse(self._ai.incubator)

    @cached_property
    def ads(self) -> AsyncAdsResourceWithRawResponse:
        return AsyncAdsResourceWithRawResponse(self._ai.ads)


class AIResourceWithStreamingResponse:
    def __init__(self, ai: AIResource) -> None:
        self._ai = ai

    @cached_property
    def advisor(self) -> AdvisorResourceWithStreamingResponse:
        return AdvisorResourceWithStreamingResponse(self._ai.advisor)

    @cached_property
    def oracle(self) -> OracleResourceWithStreamingResponse:
        return OracleResourceWithStreamingResponse(self._ai.oracle)

    @cached_property
    def incubator(self) -> IncubatorResourceWithStreamingResponse:
        return IncubatorResourceWithStreamingResponse(self._ai.incubator)

    @cached_property
    def ads(self) -> AdsResourceWithStreamingResponse:
        return AdsResourceWithStreamingResponse(self._ai.ads)


class AsyncAIResourceWithStreamingResponse:
    def __init__(self, ai: AsyncAIResource) -> None:
        self._ai = ai

    @cached_property
    def advisor(self) -> AsyncAdvisorResourceWithStreamingResponse:
        return AsyncAdvisorResourceWithStreamingResponse(self._ai.advisor)

    @cached_property
    def oracle(self) -> AsyncOracleResourceWithStreamingResponse:
        return AsyncOracleResourceWithStreamingResponse(self._ai.oracle)

    @cached_property
    def incubator(self) -> AsyncIncubatorResourceWithStreamingResponse:
        return AsyncIncubatorResourceWithStreamingResponse(self._ai.incubator)

    @cached_property
    def ads(self) -> AsyncAdsResourceWithStreamingResponse:
        return AsyncAdsResourceWithStreamingResponse(self._ai.ads)
