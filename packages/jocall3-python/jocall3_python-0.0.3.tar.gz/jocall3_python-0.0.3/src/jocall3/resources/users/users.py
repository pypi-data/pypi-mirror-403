# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .me.me import (
    MeResource,
    AsyncMeResource,
    MeResourceWithRawResponse,
    AsyncMeResourceWithRawResponse,
    MeResourceWithStreamingResponse,
    AsyncMeResourceWithStreamingResponse,
)
from ...types import user_login_params, user_register_params
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
from .password_reset import (
    PasswordResetResource,
    AsyncPasswordResetResource,
    PasswordResetResourceWithRawResponse,
    AsyncPasswordResetResourceWithRawResponse,
    PasswordResetResourceWithStreamingResponse,
    AsyncPasswordResetResourceWithStreamingResponse,
)
from ...types.user_login_response import UserLoginResponse
from ...types.user_register_response import UserRegisterResponse

__all__ = ["UsersResource", "AsyncUsersResource"]


class UsersResource(SyncAPIResource):
    @cached_property
    def password_reset(self) -> PasswordResetResource:
        return PasswordResetResource(self._client)

    @cached_property
    def me(self) -> MeResource:
        return MeResource(self._client)

    @cached_property
    def with_raw_response(self) -> UsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return UsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return UsersResourceWithStreamingResponse(self)

    def login(
        self,
        *,
        email: str,
        password: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLoginResponse:
        """Authenticates a user and creates a secure session, returning access tokens.

        May
        require MFA depending on user settings.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/users/login",
            body=maybe_transform(
                {
                    "email": email,
                    "password": password,
                },
                user_login_params.UserLoginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLoginResponse,
        )

    def register(
        self,
        *,
        email: str,
        name: str,
        password: str,
        address: user_register_params.Address | Omit = omit,
        phone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserRegisterResponse:
        """Registers a new user account with , initiating the onboarding process.

        Requires
        basic user details.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/users/register",
            body=maybe_transform(
                {
                    "email": email,
                    "name": name,
                    "password": password,
                    "address": address,
                    "phone": phone,
                },
                user_register_params.UserRegisterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserRegisterResponse,
        )


class AsyncUsersResource(AsyncAPIResource):
    @cached_property
    def password_reset(self) -> AsyncPasswordResetResource:
        return AsyncPasswordResetResource(self._client)

    @cached_property
    def me(self) -> AsyncMeResource:
        return AsyncMeResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncUsersResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUsersResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncUsersResourceWithStreamingResponse(self)

    async def login(
        self,
        *,
        email: str,
        password: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserLoginResponse:
        """Authenticates a user and creates a secure session, returning access tokens.

        May
        require MFA depending on user settings.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/users/login",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "password": password,
                },
                user_login_params.UserLoginParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserLoginResponse,
        )

    async def register(
        self,
        *,
        email: str,
        name: str,
        password: str,
        address: user_register_params.Address | Omit = omit,
        phone: str | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> UserRegisterResponse:
        """Registers a new user account with , initiating the onboarding process.

        Requires
        basic user details.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/users/register",
            body=await async_maybe_transform(
                {
                    "email": email,
                    "name": name,
                    "password": password,
                    "address": address,
                    "phone": phone,
                },
                user_register_params.UserRegisterParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserRegisterResponse,
        )


class UsersResourceWithRawResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users

        self.login = to_raw_response_wrapper(
            users.login,
        )
        self.register = to_raw_response_wrapper(
            users.register,
        )

    @cached_property
    def password_reset(self) -> PasswordResetResourceWithRawResponse:
        return PasswordResetResourceWithRawResponse(self._users.password_reset)

    @cached_property
    def me(self) -> MeResourceWithRawResponse:
        return MeResourceWithRawResponse(self._users.me)


class AsyncUsersResourceWithRawResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users

        self.login = async_to_raw_response_wrapper(
            users.login,
        )
        self.register = async_to_raw_response_wrapper(
            users.register,
        )

    @cached_property
    def password_reset(self) -> AsyncPasswordResetResourceWithRawResponse:
        return AsyncPasswordResetResourceWithRawResponse(self._users.password_reset)

    @cached_property
    def me(self) -> AsyncMeResourceWithRawResponse:
        return AsyncMeResourceWithRawResponse(self._users.me)


class UsersResourceWithStreamingResponse:
    def __init__(self, users: UsersResource) -> None:
        self._users = users

        self.login = to_streamed_response_wrapper(
            users.login,
        )
        self.register = to_streamed_response_wrapper(
            users.register,
        )

    @cached_property
    def password_reset(self) -> PasswordResetResourceWithStreamingResponse:
        return PasswordResetResourceWithStreamingResponse(self._users.password_reset)

    @cached_property
    def me(self) -> MeResourceWithStreamingResponse:
        return MeResourceWithStreamingResponse(self._users.me)


class AsyncUsersResourceWithStreamingResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        self._users = users

        self.login = async_to_streamed_response_wrapper(
            users.login,
        )
        self.register = async_to_streamed_response_wrapper(
            users.register,
        )

    @cached_property
    def password_reset(self) -> AsyncPasswordResetResourceWithStreamingResponse:
        return AsyncPasswordResetResourceWithStreamingResponse(self._users.password_reset)

    @cached_property
    def me(self) -> AsyncMeResourceWithStreamingResponse:
        return AsyncMeResourceWithStreamingResponse(self._users.me)
