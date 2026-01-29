# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...._types import Body, Query, Headers, NotGiven, not_given
from ...._utils import maybe_transform, async_maybe_transform
from ...._compat import cached_property
from ...._resource import SyncAPIResource, AsyncAPIResource
from ...._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...._base_client import make_request_options
from ....types.ai.incubator import pitch_submit_business_plan_params
from ....types.ai.incubator.pitch_retrieve_analysis_response import PitchRetrieveAnalysisResponse

__all__ = ["PitchResource", "AsyncPitchResource"]


class PitchResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> PitchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return PitchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> PitchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return PitchResourceWithStreamingResponse(self)

    def retrieve_analysis(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchRetrieveAnalysisResponse:
        """
        Retrieves the granular AI-driven analysis, strategic feedback, market validation
        results, and any outstanding questions from Quantum Weaver for a specific
        business pitch.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return self._get(
            f"/ai/incubator/pitch/{pitch_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchRetrieveAnalysisResponse,
        )

    def submit_business_plan(
        self,
        *,
        financial_projections: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Submits a detailed business plan to the Quantum Weaver AI for rigorous analysis,
        market validation, and seed funding consideration. This initiates the AI-driven
        incubation journey, aiming to transform innovative ideas into commercially
        successful ventures.

        Args:
          financial_projections: Key financial metrics and projections for the next 3-5 years.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/ai/incubator/pitch",
            body=maybe_transform(
                {"financial_projections": financial_projections},
                pitch_submit_business_plan_params.PitchSubmitBusinessPlanParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    def submit_feedback(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Allows the entrepreneur to respond to specific questions or provide additional
        details requested by Quantum Weaver, moving the pitch forward in the incubation
        process.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return self._put(
            f"/ai/incubator/pitch/{pitch_id}/feedback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class AsyncPitchResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncPitchResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncPitchResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncPitchResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncPitchResourceWithStreamingResponse(self)

    async def retrieve_analysis(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> PitchRetrieveAnalysisResponse:
        """
        Retrieves the granular AI-driven analysis, strategic feedback, market validation
        results, and any outstanding questions from Quantum Weaver for a specific
        business pitch.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return await self._get(
            f"/ai/incubator/pitch/{pitch_id}/details",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=PitchRetrieveAnalysisResponse,
        )

    async def submit_business_plan(
        self,
        *,
        financial_projections: object,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Submits a detailed business plan to the Quantum Weaver AI for rigorous analysis,
        market validation, and seed funding consideration. This initiates the AI-driven
        incubation journey, aiming to transform innovative ideas into commercially
        successful ventures.

        Args:
          financial_projections: Key financial metrics and projections for the next 3-5 years.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/ai/incubator/pitch",
            body=await async_maybe_transform(
                {"financial_projections": financial_projections},
                pitch_submit_business_plan_params.PitchSubmitBusinessPlanParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )

    async def submit_feedback(
        self,
        pitch_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Allows the entrepreneur to respond to specific questions or provide additional
        details requested by Quantum Weaver, moving the pitch forward in the incubation
        process.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not pitch_id:
            raise ValueError(f"Expected a non-empty value for `pitch_id` but received {pitch_id!r}")
        return await self._put(
            f"/ai/incubator/pitch/{pitch_id}/feedback",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=object,
        )


class PitchResourceWithRawResponse:
    def __init__(self, pitch: PitchResource) -> None:
        self._pitch = pitch

        self.retrieve_analysis = to_raw_response_wrapper(
            pitch.retrieve_analysis,
        )
        self.submit_business_plan = to_raw_response_wrapper(
            pitch.submit_business_plan,
        )
        self.submit_feedback = to_raw_response_wrapper(
            pitch.submit_feedback,
        )


class AsyncPitchResourceWithRawResponse:
    def __init__(self, pitch: AsyncPitchResource) -> None:
        self._pitch = pitch

        self.retrieve_analysis = async_to_raw_response_wrapper(
            pitch.retrieve_analysis,
        )
        self.submit_business_plan = async_to_raw_response_wrapper(
            pitch.submit_business_plan,
        )
        self.submit_feedback = async_to_raw_response_wrapper(
            pitch.submit_feedback,
        )


class PitchResourceWithStreamingResponse:
    def __init__(self, pitch: PitchResource) -> None:
        self._pitch = pitch

        self.retrieve_analysis = to_streamed_response_wrapper(
            pitch.retrieve_analysis,
        )
        self.submit_business_plan = to_streamed_response_wrapper(
            pitch.submit_business_plan,
        )
        self.submit_feedback = to_streamed_response_wrapper(
            pitch.submit_feedback,
        )


class AsyncPitchResourceWithStreamingResponse:
    def __init__(self, pitch: AsyncPitchResource) -> None:
        self._pitch = pitch

        self.retrieve_analysis = async_to_streamed_response_wrapper(
            pitch.retrieve_analysis,
        )
        self.submit_business_plan = async_to_streamed_response_wrapper(
            pitch.submit_business_plan,
        )
        self.submit_feedback = async_to_streamed_response_wrapper(
            pitch.submit_feedback,
        )
