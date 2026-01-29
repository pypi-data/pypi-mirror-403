# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from .fx import (
    FxResource,
    AsyncFxResource,
    FxResourceWithRawResponse,
    AsyncFxResourceWithRawResponse,
    FxResourceWithStreamingResponse,
    AsyncFxResourceWithStreamingResponse,
)
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from .international import (
    InternationalResource,
    AsyncInternationalResource,
    InternationalResourceWithRawResponse,
    AsyncInternationalResourceWithRawResponse,
    InternationalResourceWithStreamingResponse,
    AsyncInternationalResourceWithStreamingResponse,
)

__all__ = ["PaymentsResource", "AsyncPaymentsResource"]


class PaymentsResource(SyncAPIResource):
    @cached_property
    def international(self) -> InternationalResource:
        return InternationalResource(self._client)

    @cached_property
    def fx(self) -> FxResource:
        return FxResource(self._client)

    @cached_property
    def with_raw_response(self) -> PaymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return PaymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PaymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return PaymentsResourceWithStreamingResponse(self)


class AsyncPaymentsResource(AsyncAPIResource):
    @cached_property
    def international(self) -> AsyncInternationalResource:
        return AsyncInternationalResource(self._client)

    @cached_property
    def fx(self) -> AsyncFxResource:
        return AsyncFxResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncPaymentsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPaymentsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPaymentsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncPaymentsResourceWithStreamingResponse(self)


class PaymentsResourceWithRawResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments

    @cached_property
    def international(self) -> InternationalResourceWithRawResponse:
        return InternationalResourceWithRawResponse(self._payments.international)

    @cached_property
    def fx(self) -> FxResourceWithRawResponse:
        return FxResourceWithRawResponse(self._payments.fx)


class AsyncPaymentsResourceWithRawResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments

    @cached_property
    def international(self) -> AsyncInternationalResourceWithRawResponse:
        return AsyncInternationalResourceWithRawResponse(self._payments.international)

    @cached_property
    def fx(self) -> AsyncFxResourceWithRawResponse:
        return AsyncFxResourceWithRawResponse(self._payments.fx)


class PaymentsResourceWithStreamingResponse:
    def __init__(self, payments: PaymentsResource) -> None:
        self._payments = payments

    @cached_property
    def international(self) -> InternationalResourceWithStreamingResponse:
        return InternationalResourceWithStreamingResponse(self._payments.international)

    @cached_property
    def fx(self) -> FxResourceWithStreamingResponse:
        return FxResourceWithStreamingResponse(self._payments.fx)


class AsyncPaymentsResourceWithStreamingResponse:
    def __init__(self, payments: AsyncPaymentsResource) -> None:
        self._payments = payments

    @cached_property
    def international(self) -> AsyncInternationalResourceWithStreamingResponse:
        return AsyncInternationalResourceWithStreamingResponse(self._payments.international)

    @cached_property
    def fx(self) -> AsyncFxResourceWithStreamingResponse:
        return AsyncFxResourceWithStreamingResponse(self._payments.fx)
