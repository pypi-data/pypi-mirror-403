# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ..._types import Body, Omit, Query, Headers, NotGiven, omit, not_given
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ..._base_client import make_request_options
from ...types.accounts import overdraft_setting_update_overdraft_settings_params
from ...types.accounts.overdraft_setting_update_overdraft_settings_response import (
    OverdraftSettingUpdateOverdraftSettingsResponse,
)
from ...types.accounts.overdraft_setting_retrieve_overdraft_settings_response import (
    OverdraftSettingRetrieveOverdraftSettingsResponse,
)

__all__ = ["OverdraftSettingsResource", "AsyncOverdraftSettingsResource"]


class OverdraftSettingsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> OverdraftSettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return OverdraftSettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> OverdraftSettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return OverdraftSettingsResourceWithStreamingResponse(self)

    def retrieve_overdraft_settings(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OverdraftSettingRetrieveOverdraftSettingsResponse:
        """
        Retrieves the current overdraft protection settings for a specific account.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._get(
            f"/accounts/{account_id}/overdraft-settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OverdraftSettingRetrieveOverdraftSettingsResponse,
        )

    def update_overdraft_settings(
        self,
        account_id: str,
        *,
        enabled: bool | Omit = omit,
        fee_preference: str | Omit = omit,
        link_to_savings: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OverdraftSettingUpdateOverdraftSettingsResponse:
        """
        Updates the overdraft protection settings for a specific account, enabling or
        disabling protection and configuring preferences.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return self._put(
            f"/accounts/{account_id}/overdraft-settings",
            body=maybe_transform(
                {
                    "enabled": enabled,
                    "fee_preference": fee_preference,
                    "link_to_savings": link_to_savings,
                },
                overdraft_setting_update_overdraft_settings_params.OverdraftSettingUpdateOverdraftSettingsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OverdraftSettingUpdateOverdraftSettingsResponse,
        )


class AsyncOverdraftSettingsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncOverdraftSettingsResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncOverdraftSettingsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncOverdraftSettingsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncOverdraftSettingsResourceWithStreamingResponse(self)

    async def retrieve_overdraft_settings(
        self,
        account_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OverdraftSettingRetrieveOverdraftSettingsResponse:
        """
        Retrieves the current overdraft protection settings for a specific account.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._get(
            f"/accounts/{account_id}/overdraft-settings",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OverdraftSettingRetrieveOverdraftSettingsResponse,
        )

    async def update_overdraft_settings(
        self,
        account_id: str,
        *,
        enabled: bool | Omit = omit,
        fee_preference: str | Omit = omit,
        link_to_savings: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> OverdraftSettingUpdateOverdraftSettingsResponse:
        """
        Updates the overdraft protection settings for a specific account, enabling or
        disabling protection and configuring preferences.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not account_id:
            raise ValueError(f"Expected a non-empty value for `account_id` but received {account_id!r}")
        return await self._put(
            f"/accounts/{account_id}/overdraft-settings",
            body=await async_maybe_transform(
                {
                    "enabled": enabled,
                    "fee_preference": fee_preference,
                    "link_to_savings": link_to_savings,
                },
                overdraft_setting_update_overdraft_settings_params.OverdraftSettingUpdateOverdraftSettingsParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=OverdraftSettingUpdateOverdraftSettingsResponse,
        )


class OverdraftSettingsResourceWithRawResponse:
    def __init__(self, overdraft_settings: OverdraftSettingsResource) -> None:
        self._overdraft_settings = overdraft_settings

        self.retrieve_overdraft_settings = to_raw_response_wrapper(
            overdraft_settings.retrieve_overdraft_settings,
        )
        self.update_overdraft_settings = to_raw_response_wrapper(
            overdraft_settings.update_overdraft_settings,
        )


class AsyncOverdraftSettingsResourceWithRawResponse:
    def __init__(self, overdraft_settings: AsyncOverdraftSettingsResource) -> None:
        self._overdraft_settings = overdraft_settings

        self.retrieve_overdraft_settings = async_to_raw_response_wrapper(
            overdraft_settings.retrieve_overdraft_settings,
        )
        self.update_overdraft_settings = async_to_raw_response_wrapper(
            overdraft_settings.update_overdraft_settings,
        )


class OverdraftSettingsResourceWithStreamingResponse:
    def __init__(self, overdraft_settings: OverdraftSettingsResource) -> None:
        self._overdraft_settings = overdraft_settings

        self.retrieve_overdraft_settings = to_streamed_response_wrapper(
            overdraft_settings.retrieve_overdraft_settings,
        )
        self.update_overdraft_settings = to_streamed_response_wrapper(
            overdraft_settings.update_overdraft_settings,
        )


class AsyncOverdraftSettingsResourceWithStreamingResponse:
    def __init__(self, overdraft_settings: AsyncOverdraftSettingsResource) -> None:
        self._overdraft_settings = overdraft_settings

        self.retrieve_overdraft_settings = async_to_streamed_response_wrapper(
            overdraft_settings.retrieve_overdraft_settings,
        )
        self.update_overdraft_settings = async_to_streamed_response_wrapper(
            overdraft_settings.update_overdraft_settings,
        )
