# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from ...types import web3_retrieve_nfts_params
from .wallets import (
    WalletsResource,
    AsyncWalletsResource,
    WalletsResourceWithRawResponse,
    AsyncWalletsResourceWithRawResponse,
    WalletsResourceWithStreamingResponse,
    AsyncWalletsResourceWithStreamingResponse,
)
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
from .transactions import (
    TransactionsResource,
    AsyncTransactionsResource,
    TransactionsResourceWithRawResponse,
    AsyncTransactionsResourceWithRawResponse,
    TransactionsResourceWithStreamingResponse,
    AsyncTransactionsResourceWithStreamingResponse,
)
from ..._base_client import make_request_options

__all__ = ["Web3Resource", "AsyncWeb3Resource"]


class Web3Resource(SyncAPIResource):
    @cached_property
    def wallets(self) -> WalletsResource:
        return WalletsResource(self._client)

    @cached_property
    def transactions(self) -> TransactionsResource:
        return TransactionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> Web3ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return Web3ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> Web3ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return Web3ResourceWithStreamingResponse(self)

    def retrieve_nfts(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Fetches a comprehensive list of Non-Fungible Tokens (NFTs) owned by the user
        across all connected wallets and supported blockchain networks, including
        metadata and market values.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._get(
            "/web3/nfts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    web3_retrieve_nfts_params.Web3RetrieveNFTsParams,
                ),
            ),
            cast_to=object,
        )


class AsyncWeb3Resource(AsyncAPIResource):
    @cached_property
    def wallets(self) -> AsyncWalletsResource:
        return AsyncWalletsResource(self._client)

    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        return AsyncTransactionsResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncWeb3ResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWeb3ResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWeb3ResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/diplomat-bit/jocall3-python#with_streaming_response
        """
        return AsyncWeb3ResourceWithStreamingResponse(self)

    async def retrieve_nfts(
        self,
        *,
        limit: int | Omit = omit,
        offset: int | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> object:
        """
        Fetches a comprehensive list of Non-Fungible Tokens (NFTs) owned by the user
        across all connected wallets and supported blockchain networks, including
        metadata and market values.

        Args:
          limit: Maximum number of items to return in a single page.

          offset: Number of items to skip before starting to collect the result set.

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._get(
            "/web3/nfts",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "limit": limit,
                        "offset": offset,
                    },
                    web3_retrieve_nfts_params.Web3RetrieveNFTsParams,
                ),
            ),
            cast_to=object,
        )


class Web3ResourceWithRawResponse:
    def __init__(self, web3: Web3Resource) -> None:
        self._web3 = web3

        self.retrieve_nfts = to_raw_response_wrapper(
            web3.retrieve_nfts,
        )

    @cached_property
    def wallets(self) -> WalletsResourceWithRawResponse:
        return WalletsResourceWithRawResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> TransactionsResourceWithRawResponse:
        return TransactionsResourceWithRawResponse(self._web3.transactions)


class AsyncWeb3ResourceWithRawResponse:
    def __init__(self, web3: AsyncWeb3Resource) -> None:
        self._web3 = web3

        self.retrieve_nfts = async_to_raw_response_wrapper(
            web3.retrieve_nfts,
        )

    @cached_property
    def wallets(self) -> AsyncWalletsResourceWithRawResponse:
        return AsyncWalletsResourceWithRawResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithRawResponse:
        return AsyncTransactionsResourceWithRawResponse(self._web3.transactions)


class Web3ResourceWithStreamingResponse:
    def __init__(self, web3: Web3Resource) -> None:
        self._web3 = web3

        self.retrieve_nfts = to_streamed_response_wrapper(
            web3.retrieve_nfts,
        )

    @cached_property
    def wallets(self) -> WalletsResourceWithStreamingResponse:
        return WalletsResourceWithStreamingResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> TransactionsResourceWithStreamingResponse:
        return TransactionsResourceWithStreamingResponse(self._web3.transactions)


class AsyncWeb3ResourceWithStreamingResponse:
    def __init__(self, web3: AsyncWeb3Resource) -> None:
        self._web3 = web3

        self.retrieve_nfts = async_to_streamed_response_wrapper(
            web3.retrieve_nfts,
        )

    @cached_property
    def wallets(self) -> AsyncWalletsResourceWithStreamingResponse:
        return AsyncWalletsResourceWithStreamingResponse(self._web3.wallets)

    @cached_property
    def transactions(self) -> AsyncTransactionsResourceWithStreamingResponse:
        return AsyncTransactionsResourceWithStreamingResponse(self._web3.transactions)
