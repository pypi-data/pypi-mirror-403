# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .pitch import (
    PitchResource,
    AsyncPitchResource,
    PitchResourceWithRawResponse,
    AsyncPitchResourceWithRawResponse,
    PitchResourceWithStreamingResponse,
    AsyncPitchResourceWithStreamingResponse,
)
from ...._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ....types.ai import incubator_list_pitches_params
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options

__all__ = ["IncubatorResource", "AsyncIncubatorResource"]


class IncubatorResource(SyncAPIResource):
    @cached_property
    def pitch(self) -> PitchResource:
        return PitchResource(self._client)

    @cached_property
    def with_raw_response(self) -> IncubatorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return IncubatorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> IncubatorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return IncubatorResourceWithStreamingResponse(self)

    def list_pitches(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a summary list of all business pitches submitted by the authenticated
        user to Quantum Weaver.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          status: Filter pitches by their current stage.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/ai/incubator/pitches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                        "status": status,
                    },
                    incubator_list_pitches_params.IncubatorListPitchesParams,
                ),
            ),
            cast_to=object,
        )


class AsyncIncubatorResource(AsyncAPIResource):
    @cached_property
    def pitch(self) -> AsyncPitchResource:
        return AsyncPitchResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncIncubatorResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncIncubatorResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncIncubatorResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncIncubatorResourceWithStreamingResponse(self)

    async def list_pitches(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        status: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Retrieves a summary list of all business pitches submitted by the authenticated
        user to Quantum Weaver.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          status: Filter pitches by their current stage.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/ai/incubator/pitches",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                        "status": status,
                    },
                    incubator_list_pitches_params.IncubatorListPitchesParams,
                ),
            ),
            cast_to=object,
        )


class IncubatorResourceWithRawResponse:
    def __init__(self, incubator: IncubatorResource) -> None:
        self._incubator = incubator

        self.list_pitches = to_raw_response_wrapper(
            incubator.list_pitches,
        )

    @cached_property
    def pitch(self) -> PitchResourceWithRawResponse:
        return PitchResourceWithRawResponse(self._incubator.pitch)


class AsyncIncubatorResourceWithRawResponse:
    def __init__(self, incubator: AsyncIncubatorResource) -> None:
        self._incubator = incubator

        self.list_pitches = async_to_raw_response_wrapper(
            incubator.list_pitches,
        )

    @cached_property
    def pitch(self) -> AsyncPitchResourceWithRawResponse:
        return AsyncPitchResourceWithRawResponse(self._incubator.pitch)


class IncubatorResourceWithStreamingResponse:
    def __init__(self, incubator: IncubatorResource) -> None:
        self._incubator = incubator

        self.list_pitches = to_streamed_response_wrapper(
            incubator.list_pitches,
        )

    @cached_property
    def pitch(self) -> PitchResourceWithStreamingResponse:
        return PitchResourceWithStreamingResponse(self._incubator.pitch)


class AsyncIncubatorResourceWithStreamingResponse:
    def __init__(self, incubator: AsyncIncubatorResource) -> None:
        self._incubator = incubator

        self.list_pitches = async_to_streamed_response_wrapper(
            incubator.list_pitches,
        )

    @cached_property
    def pitch(self) -> AsyncPitchResourceWithStreamingResponse:
        return AsyncPitchResourceWithStreamingResponse(self._incubator.pitch)
