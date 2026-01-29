# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .cards import (
    CardsResource,
    AsyncCardsResource,
    CardsResourceWithRawResponse,
    AsyncCardsResourceWithRawResponse,
    CardsResourceWithStreamingResponse,
    AsyncCardsResourceWithStreamingResponse,
)
from ...types import corporate_perform_sanction_screening_params
from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from .anomalies import (
    AnomaliesResource,
    AsyncAnomaliesResource,
    AnomaliesResourceWithRawResponse,
    AsyncAnomaliesResourceWithRawResponse,
    AnomaliesResourceWithStreamingResponse,
    AsyncAnomaliesResourceWithStreamingResponse,
)
from .risk.risk import (
    RiskResource,
    AsyncRiskResource,
    RiskResourceWithRawResponse,
    AsyncRiskResourceWithRawResponse,
    RiskResourceWithStreamingResponse,
    AsyncRiskResourceWithStreamingResponse,
)
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from .treasury.treasury import (
    TreasuryResource,
    AsyncTreasuryResource,
    TreasuryResourceWithRawResponse,
    AsyncTreasuryResourceWithRawResponse,
    TreasuryResourceWithStreamingResponse,
    AsyncTreasuryResourceWithStreamingResponse,
)
from .compliance.compliance import (
    ComplianceResource,
    AsyncComplianceResource,
    ComplianceResourceWithRawResponse,
    AsyncComplianceResourceWithRawResponse,
    ComplianceResourceWithStreamingResponse,
    AsyncComplianceResourceWithStreamingResponse,
)

__all__ = ["CorporateResource", "AsyncCorporateResource"]


class CorporateResource(SyncAPIResource):
    @cached_property
    def cards(self) -> CardsResource:
        return CardsResource(self._client)

    @cached_property
    def anomalies(self) -> AnomaliesResource:
        return AnomaliesResource(self._client)

    @cached_property
    def compliance(self) -> ComplianceResource:
        return ComplianceResource(self._client)

    @cached_property
    def treasury(self) -> TreasuryResource:
        return TreasuryResource(self._client)

    @cached_property
    def risk(self) -> RiskResource:
        return RiskResource(self._client)

    @cached_property
    def with_raw_response(self) -> CorporateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return CorporateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> CorporateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return CorporateResourceWithStreamingResponse(self)

    def perform_sanction_screening(
        self,
        *,
        address: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Executes a real-time screening of an individual or entity against global
        sanction lists and watchlists.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/corporate/sanction-screening",
            body=maybe_transform(
                {"address": address},
                corporate_perform_sanction_screening_params.CorporatePerformSanctionScreeningParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncCorporateResource(AsyncAPIResource):
    @cached_property
    def cards(self) -> AsyncCardsResource:
        return AsyncCardsResource(self._client)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResource:
        return AsyncAnomaliesResource(self._client)

    @cached_property
    def compliance(self) -> AsyncComplianceResource:
        return AsyncComplianceResource(self._client)

    @cached_property
    def treasury(self) -> AsyncTreasuryResource:
        return AsyncTreasuryResource(self._client)

    @cached_property
    def risk(self) -> AsyncRiskResource:
        return AsyncRiskResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncCorporateResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncCorporateResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncCorporateResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncCorporateResourceWithStreamingResponse(self)

    async def perform_sanction_screening(
        self,
        *,
        address: object | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Executes a real-time screening of an individual or entity against global
        sanction lists and watchlists.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/corporate/sanction-screening",
            body=await async_maybe_transform(
                {"address": address},
                corporate_perform_sanction_screening_params.CorporatePerformSanctionScreeningParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class CorporateResourceWithRawResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

        self.perform_sanction_screening = to_raw_response_wrapper(
            corporate.perform_sanction_screening,
        )

    @cached_property
    def cards(self) -> CardsResourceWithRawResponse:
        return CardsResourceWithRawResponse(self._corporate.cards)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithRawResponse:
        return AnomaliesResourceWithRawResponse(self._corporate.anomalies)

    @cached_property
    def compliance(self) -> ComplianceResourceWithRawResponse:
        return ComplianceResourceWithRawResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> TreasuryResourceWithRawResponse:
        return TreasuryResourceWithRawResponse(self._corporate.treasury)

    @cached_property
    def risk(self) -> RiskResourceWithRawResponse:
        return RiskResourceWithRawResponse(self._corporate.risk)


class AsyncCorporateResourceWithRawResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

        self.perform_sanction_screening = async_to_raw_response_wrapper(
            corporate.perform_sanction_screening,
        )

    @cached_property
    def cards(self) -> AsyncCardsResourceWithRawResponse:
        return AsyncCardsResourceWithRawResponse(self._corporate.cards)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithRawResponse:
        return AsyncAnomaliesResourceWithRawResponse(self._corporate.anomalies)

    @cached_property
    def compliance(self) -> AsyncComplianceResourceWithRawResponse:
        return AsyncComplianceResourceWithRawResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> AsyncTreasuryResourceWithRawResponse:
        return AsyncTreasuryResourceWithRawResponse(self._corporate.treasury)

    @cached_property
    def risk(self) -> AsyncRiskResourceWithRawResponse:
        return AsyncRiskResourceWithRawResponse(self._corporate.risk)


class CorporateResourceWithStreamingResponse:
    def __init__(self, corporate: CorporateResource) -> None:
        self._corporate = corporate

        self.perform_sanction_screening = to_streamed_response_wrapper(
            corporate.perform_sanction_screening,
        )

    @cached_property
    def cards(self) -> CardsResourceWithStreamingResponse:
        return CardsResourceWithStreamingResponse(self._corporate.cards)

    @cached_property
    def anomalies(self) -> AnomaliesResourceWithStreamingResponse:
        return AnomaliesResourceWithStreamingResponse(self._corporate.anomalies)

    @cached_property
    def compliance(self) -> ComplianceResourceWithStreamingResponse:
        return ComplianceResourceWithStreamingResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> TreasuryResourceWithStreamingResponse:
        return TreasuryResourceWithStreamingResponse(self._corporate.treasury)

    @cached_property
    def risk(self) -> RiskResourceWithStreamingResponse:
        return RiskResourceWithStreamingResponse(self._corporate.risk)


class AsyncCorporateResourceWithStreamingResponse:
    def __init__(self, corporate: AsyncCorporateResource) -> None:
        self._corporate = corporate

        self.perform_sanction_screening = async_to_streamed_response_wrapper(
            corporate.perform_sanction_screening,
        )

    @cached_property
    def cards(self) -> AsyncCardsResourceWithStreamingResponse:
        return AsyncCardsResourceWithStreamingResponse(self._corporate.cards)

    @cached_property
    def anomalies(self) -> AsyncAnomaliesResourceWithStreamingResponse:
        return AsyncAnomaliesResourceWithStreamingResponse(self._corporate.anomalies)

    @cached_property
    def compliance(self) -> AsyncComplianceResourceWithStreamingResponse:
        return AsyncComplianceResourceWithStreamingResponse(self._corporate.compliance)

    @cached_property
    def treasury(self) -> AsyncTreasuryResourceWithStreamingResponse:
        return AsyncTreasuryResourceWithStreamingResponse(self._corporate.treasury)

    @cached_property
    def risk(self) -> AsyncRiskResourceWithStreamingResponse:
        return AsyncRiskResourceWithStreamingResponse(self._corporate.risk)
