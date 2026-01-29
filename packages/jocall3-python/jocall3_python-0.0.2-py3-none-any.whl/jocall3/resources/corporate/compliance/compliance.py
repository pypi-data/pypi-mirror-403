# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .audits import (
    AuditsResource,
    AsyncAuditsResource,
    AuditsResourceWithRawResponse,
    AsyncAuditsResourceWithRawResponse,
    AuditsResourceWithStreamingResponse,
    AsyncAuditsResourceWithStreamingResponse,
)
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource

__all__ = ["ComplianceResource", "AsyncComplianceResource"]


class ComplianceResource(SyncAPIResource):
    @cached_property
    def audits(self) -> AuditsResource:
        return AuditsResource(self._client)

    @cached_property
    def with_raw_response(self) -> ComplianceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return ComplianceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> ComplianceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return ComplianceResourceWithStreamingResponse(self)


class AsyncComplianceResource(AsyncAPIResource):
    @cached_property
    def audits(self) -> AsyncAuditsResource:
        return AsyncAuditsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncComplianceResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncComplianceResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncComplianceResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncComplianceResourceWithStreamingResponse(self)


class ComplianceResourceWithRawResponse:
    def __init__(self, compliance: ComplianceResource) -> None:
        self._compliance = compliance

    @cached_property
    def audits(self) -> AuditsResourceWithRawResponse:
        return AuditsResourceWithRawResponse(self._compliance.audits)


class AsyncComplianceResourceWithRawResponse:
    def __init__(self, compliance: AsyncComplianceResource) -> None:
        self._compliance = compliance

    @cached_property
    def audits(self) -> AsyncAuditsResourceWithRawResponse:
        return AsyncAuditsResourceWithRawResponse(self._compliance.audits)


class ComplianceResourceWithStreamingResponse:
    def __init__(self, compliance: ComplianceResource) -> None:
        self._compliance = compliance

    @cached_property
    def audits(self) -> AuditsResourceWithStreamingResponse:
        return AuditsResourceWithStreamingResponse(self._compliance.audits)


class AsyncComplianceResourceWithStreamingResponse:
    def __init__(self, compliance: AsyncComplianceResource) -> None:
        self._compliance = compliance

    @cached_property
    def audits(self) -> AsyncAuditsResourceWithStreamingResponse:
        return AsyncAuditsResourceWithStreamingResponse(self._compliance.audits)
