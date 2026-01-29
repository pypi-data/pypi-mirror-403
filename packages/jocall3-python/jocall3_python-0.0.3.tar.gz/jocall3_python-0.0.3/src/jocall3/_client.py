# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Any, Mapping
from typing_extensions import Self, override

import httpx

from . import _exceptions
from ._qs import Querystring
from ._types import (
    Omit,
    Headers,
    Timeout,
    NotGiven,
    Transport,
    ProxiesTypes,
    RequestOptions,
    not_given,
)
from ._utils import is_given, get_async_library
from ._compat import cached_property
from ._version import __version__
from ._streaming import Stream as Stream, AsyncStream as AsyncStream
from ._exceptions import APIStatusError
from ._base_client import (
    DEFAULT_MAX_RETRIES,
    SyncAPIClient,
    AsyncAPIClient,
)

if TYPE_CHECKING:
    from .resources import (
        ai,
        web3,
        users,
        budgets,
        accounts,
        payments,
        corporate,
        investments,
        transactions,
        sustainability,
    )
    from .resources.ai.ai import AIResource, AsyncAIResource
    from .resources.budgets import BudgetsResource, AsyncBudgetsResource
    from .resources.web3.web3 import Web3Resource, AsyncWeb3Resource
    from .resources.users.users import UsersResource, AsyncUsersResource
    from .resources.accounts.accounts import AccountsResource, AsyncAccountsResource
    from .resources.payments.payments import PaymentsResource, AsyncPaymentsResource
    from .resources.corporate.corporate import CorporateResource, AsyncCorporateResource
    from .resources.investments.investments import InvestmentsResource, AsyncInvestmentsResource
    from .resources.transactions.transactions import TransactionsResource, AsyncTransactionsResource
    from .resources.sustainability.sustainability import SustainabilityResource, AsyncSustainabilityResource

__all__ = ["Timeout", "Transport", "ProxiesTypes", "RequestOptions", "Jocall3", "AsyncJocall3", "Client", "AsyncClient"]


class Jocall3(SyncAPIClient):
    # client options
    api_key: str | None

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#client) for more details.
        http_client: httpx.Client | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new synchronous Jocall3 client instance.

        This automatically infers the `api_key` argument from the `JOCALL3_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("JOCALL3_API_KEY")
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("JOCALL3_BASE_URL")
        if base_url is None:
            base_url = f"https://ce47fe80-dabc-4ad0-b0e7-cf285695b8b8.mock.pstmn.io"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def users(self) -> UsersResource:
        from .resources.users import UsersResource

        return UsersResource(self)

    @cached_property
    def accounts(self) -> AccountsResource:
        from .resources.accounts import AccountsResource

        return AccountsResource(self)

    @cached_property
    def transactions(self) -> TransactionsResource:
        from .resources.transactions import TransactionsResource

        return TransactionsResource(self)

    @cached_property
    def budgets(self) -> BudgetsResource:
        from .resources.budgets import BudgetsResource

        return BudgetsResource(self)

    @cached_property
    def investments(self) -> InvestmentsResource:
        from .resources.investments import InvestmentsResource

        return InvestmentsResource(self)

    @cached_property
    def ai(self) -> AIResource:
        from .resources.ai import AIResource

        return AIResource(self)

    @cached_property
    def corporate(self) -> CorporateResource:
        from .resources.corporate import CorporateResource

        return CorporateResource(self)

    @cached_property
    def web3(self) -> Web3Resource:
        from .resources.web3 import Web3Resource

        return Web3Resource(self)

    @cached_property
    def payments(self) -> PaymentsResource:
        from .resources.payments import PaymentsResource

        return PaymentsResource(self)

    @cached_property
    def sustainability(self) -> SustainabilityResource:
        from .resources.sustainability import SustainabilityResource

        return SustainabilityResource(self)

    @cached_property
    def with_raw_response(self) -> Jocall3WithRawResponse:
        return Jocall3WithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> Jocall3WithStreamedResponse:
        return Jocall3WithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if api_key is None:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": "false",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if headers.get("Authorization") or isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.Client | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class AsyncJocall3(AsyncAPIClient):
    # client options
    api_key: str | None

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        # Configure a custom httpx client.
        # We provide a `DefaultAsyncHttpxClient` class that you can pass to retain the default values we use for `limits`, `timeout` & `follow_redirects`.
        # See the [httpx documentation](https://www.python-httpx.org/api/#asyncclient) for more details.
        http_client: httpx.AsyncClient | None = None,
        # Enable or disable schema validation for data returned by the API.
        # When enabled an error APIResponseValidationError is raised
        # if the API responds with invalid data for the expected schema.
        #
        # This parameter may be removed or changed in the future.
        # If you rely on this feature, please open a GitHub issue
        # outlining your use-case to help us decide if it should be
        # part of our public interface in the future.
        _strict_response_validation: bool = False,
    ) -> None:
        """Construct a new async AsyncJocall3 client instance.

        This automatically infers the `api_key` argument from the `JOCALL3_API_KEY` environment variable if it is not provided.
        """
        if api_key is None:
            api_key = os.environ.get("JOCALL3_API_KEY")
        self.api_key = api_key

        if base_url is None:
            base_url = os.environ.get("JOCALL3_BASE_URL")
        if base_url is None:
            base_url = f"https://ce47fe80-dabc-4ad0-b0e7-cf285695b8b8.mock.pstmn.io"

        super().__init__(
            version=__version__,
            base_url=base_url,
            max_retries=max_retries,
            timeout=timeout,
            http_client=http_client,
            custom_headers=default_headers,
            custom_query=default_query,
            _strict_response_validation=_strict_response_validation,
        )

    @cached_property
    def users(self) -> AsyncUsersResource:
        from .resources.users import AsyncUsersResource

        return AsyncUsersResource(self)

    @cached_property
    def accounts(self) -> AsyncAccountsResource:
        from .resources.accounts import AsyncAccountsResource

        return AsyncAccountsResource(self)

    @cached_property
    def transactions(self) -> AsyncTransactionsResource:
        from .resources.transactions import AsyncTransactionsResource

        return AsyncTransactionsResource(self)

    @cached_property
    def budgets(self) -> AsyncBudgetsResource:
        from .resources.budgets import AsyncBudgetsResource

        return AsyncBudgetsResource(self)

    @cached_property
    def investments(self) -> AsyncInvestmentsResource:
        from .resources.investments import AsyncInvestmentsResource

        return AsyncInvestmentsResource(self)

    @cached_property
    def ai(self) -> AsyncAIResource:
        from .resources.ai import AsyncAIResource

        return AsyncAIResource(self)

    @cached_property
    def corporate(self) -> AsyncCorporateResource:
        from .resources.corporate import AsyncCorporateResource

        return AsyncCorporateResource(self)

    @cached_property
    def web3(self) -> AsyncWeb3Resource:
        from .resources.web3 import AsyncWeb3Resource

        return AsyncWeb3Resource(self)

    @cached_property
    def payments(self) -> AsyncPaymentsResource:
        from .resources.payments import AsyncPaymentsResource

        return AsyncPaymentsResource(self)

    @cached_property
    def sustainability(self) -> AsyncSustainabilityResource:
        from .resources.sustainability import AsyncSustainabilityResource

        return AsyncSustainabilityResource(self)

    @cached_property
    def with_raw_response(self) -> AsyncJocall3WithRawResponse:
        return AsyncJocall3WithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncJocall3WithStreamedResponse:
        return AsyncJocall3WithStreamedResponse(self)

    @property
    @override
    def qs(self) -> Querystring:
        return Querystring(array_format="comma")

    @property
    @override
    def auth_headers(self) -> dict[str, str]:
        api_key = self.api_key
        if api_key is None:
            return {}
        return {"Authorization": f"Bearer {api_key}"}

    @property
    @override
    def default_headers(self) -> dict[str, str | Omit]:
        return {
            **super().default_headers,
            "X-Stainless-Async": f"async:{get_async_library()}",
            **self._custom_headers,
        }

    @override
    def _validate_headers(self, headers: Headers, custom_headers: Headers) -> None:
        if headers.get("Authorization") or isinstance(custom_headers.get("Authorization"), Omit):
            return

        raise TypeError(
            '"Could not resolve authentication method. Expected the api_key to be set. Or for the `Authorization` headers to be explicitly omitted"'
        )

    def copy(
        self,
        *,
        api_key: str | None = None,
        base_url: str | httpx.URL | None = None,
        timeout: float | Timeout | None | NotGiven = not_given,
        http_client: httpx.AsyncClient | None = None,
        max_retries: int | NotGiven = not_given,
        default_headers: Mapping[str, str] | None = None,
        set_default_headers: Mapping[str, str] | None = None,
        default_query: Mapping[str, object] | None = None,
        set_default_query: Mapping[str, object] | None = None,
        _extra_kwargs: Mapping[str, Any] = {},
    ) -> Self:
        """
        Create a new client instance re-using the same options given to the current client with optional overriding.
        """
        if default_headers is not None and set_default_headers is not None:
            raise ValueError("The `default_headers` and `set_default_headers` arguments are mutually exclusive")

        if default_query is not None and set_default_query is not None:
            raise ValueError("The `default_query` and `set_default_query` arguments are mutually exclusive")

        headers = self._custom_headers
        if default_headers is not None:
            headers = {**headers, **default_headers}
        elif set_default_headers is not None:
            headers = set_default_headers

        params = self._custom_query
        if default_query is not None:
            params = {**params, **default_query}
        elif set_default_query is not None:
            params = set_default_query

        http_client = http_client or self._client
        return self.__class__(
            api_key=api_key or self.api_key,
            base_url=base_url or self.base_url,
            timeout=self.timeout if isinstance(timeout, NotGiven) else timeout,
            http_client=http_client,
            max_retries=max_retries if is_given(max_retries) else self.max_retries,
            default_headers=headers,
            default_query=params,
            **_extra_kwargs,
        )

    # Alias for `copy` for nicer inline usage, e.g.
    # client.with_options(timeout=10).foo.create(...)
    with_options = copy

    @override
    def _make_status_error(
        self,
        err_msg: str,
        *,
        body: object,
        response: httpx.Response,
    ) -> APIStatusError:
        if response.status_code == 400:
            return _exceptions.BadRequestError(err_msg, response=response, body=body)

        if response.status_code == 401:
            return _exceptions.AuthenticationError(err_msg, response=response, body=body)

        if response.status_code == 403:
            return _exceptions.PermissionDeniedError(err_msg, response=response, body=body)

        if response.status_code == 404:
            return _exceptions.NotFoundError(err_msg, response=response, body=body)

        if response.status_code == 409:
            return _exceptions.ConflictError(err_msg, response=response, body=body)

        if response.status_code == 422:
            return _exceptions.UnprocessableEntityError(err_msg, response=response, body=body)

        if response.status_code == 429:
            return _exceptions.RateLimitError(err_msg, response=response, body=body)

        if response.status_code >= 500:
            return _exceptions.InternalServerError(err_msg, response=response, body=body)
        return APIStatusError(err_msg, response=response, body=body)


class Jocall3WithRawResponse:
    _client: Jocall3

    def __init__(self, client: Jocall3) -> None:
        self._client = client

    @cached_property
    def users(self) -> users.UsersResourceWithRawResponse:
        from .resources.users import UsersResourceWithRawResponse

        return UsersResourceWithRawResponse(self._client.users)

    @cached_property
    def accounts(self) -> accounts.AccountsResourceWithRawResponse:
        from .resources.accounts import AccountsResourceWithRawResponse

        return AccountsResourceWithRawResponse(self._client.accounts)

    @cached_property
    def transactions(self) -> transactions.TransactionsResourceWithRawResponse:
        from .resources.transactions import TransactionsResourceWithRawResponse

        return TransactionsResourceWithRawResponse(self._client.transactions)

    @cached_property
    def budgets(self) -> budgets.BudgetsResourceWithRawResponse:
        from .resources.budgets import BudgetsResourceWithRawResponse

        return BudgetsResourceWithRawResponse(self._client.budgets)

    @cached_property
    def investments(self) -> investments.InvestmentsResourceWithRawResponse:
        from .resources.investments import InvestmentsResourceWithRawResponse

        return InvestmentsResourceWithRawResponse(self._client.investments)

    @cached_property
    def ai(self) -> ai.AIResourceWithRawResponse:
        from .resources.ai import AIResourceWithRawResponse

        return AIResourceWithRawResponse(self._client.ai)

    @cached_property
    def corporate(self) -> corporate.CorporateResourceWithRawResponse:
        from .resources.corporate import CorporateResourceWithRawResponse

        return CorporateResourceWithRawResponse(self._client.corporate)

    @cached_property
    def web3(self) -> web3.Web3ResourceWithRawResponse:
        from .resources.web3 import Web3ResourceWithRawResponse

        return Web3ResourceWithRawResponse(self._client.web3)

    @cached_property
    def payments(self) -> payments.PaymentsResourceWithRawResponse:
        from .resources.payments import PaymentsResourceWithRawResponse

        return PaymentsResourceWithRawResponse(self._client.payments)

    @cached_property
    def sustainability(self) -> sustainability.SustainabilityResourceWithRawResponse:
        from .resources.sustainability import SustainabilityResourceWithRawResponse

        return SustainabilityResourceWithRawResponse(self._client.sustainability)


class AsyncJocall3WithRawResponse:
    _client: AsyncJocall3

    def __init__(self, client: AsyncJocall3) -> None:
        self._client = client

    @cached_property
    def users(self) -> users.AsyncUsersResourceWithRawResponse:
        from .resources.users import AsyncUsersResourceWithRawResponse

        return AsyncUsersResourceWithRawResponse(self._client.users)

    @cached_property
    def accounts(self) -> accounts.AsyncAccountsResourceWithRawResponse:
        from .resources.accounts import AsyncAccountsResourceWithRawResponse

        return AsyncAccountsResourceWithRawResponse(self._client.accounts)

    @cached_property
    def transactions(self) -> transactions.AsyncTransactionsResourceWithRawResponse:
        from .resources.transactions import AsyncTransactionsResourceWithRawResponse

        return AsyncTransactionsResourceWithRawResponse(self._client.transactions)

    @cached_property
    def budgets(self) -> budgets.AsyncBudgetsResourceWithRawResponse:
        from .resources.budgets import AsyncBudgetsResourceWithRawResponse

        return AsyncBudgetsResourceWithRawResponse(self._client.budgets)

    @cached_property
    def investments(self) -> investments.AsyncInvestmentsResourceWithRawResponse:
        from .resources.investments import AsyncInvestmentsResourceWithRawResponse

        return AsyncInvestmentsResourceWithRawResponse(self._client.investments)

    @cached_property
    def ai(self) -> ai.AsyncAIResourceWithRawResponse:
        from .resources.ai import AsyncAIResourceWithRawResponse

        return AsyncAIResourceWithRawResponse(self._client.ai)

    @cached_property
    def corporate(self) -> corporate.AsyncCorporateResourceWithRawResponse:
        from .resources.corporate import AsyncCorporateResourceWithRawResponse

        return AsyncCorporateResourceWithRawResponse(self._client.corporate)

    @cached_property
    def web3(self) -> web3.AsyncWeb3ResourceWithRawResponse:
        from .resources.web3 import AsyncWeb3ResourceWithRawResponse

        return AsyncWeb3ResourceWithRawResponse(self._client.web3)

    @cached_property
    def payments(self) -> payments.AsyncPaymentsResourceWithRawResponse:
        from .resources.payments import AsyncPaymentsResourceWithRawResponse

        return AsyncPaymentsResourceWithRawResponse(self._client.payments)

    @cached_property
    def sustainability(self) -> sustainability.AsyncSustainabilityResourceWithRawResponse:
        from .resources.sustainability import AsyncSustainabilityResourceWithRawResponse

        return AsyncSustainabilityResourceWithRawResponse(self._client.sustainability)


class Jocall3WithStreamedResponse:
    _client: Jocall3

    def __init__(self, client: Jocall3) -> None:
        self._client = client

    @cached_property
    def users(self) -> users.UsersResourceWithStreamingResponse:
        from .resources.users import UsersResourceWithStreamingResponse

        return UsersResourceWithStreamingResponse(self._client.users)

    @cached_property
    def accounts(self) -> accounts.AccountsResourceWithStreamingResponse:
        from .resources.accounts import AccountsResourceWithStreamingResponse

        return AccountsResourceWithStreamingResponse(self._client.accounts)

    @cached_property
    def transactions(self) -> transactions.TransactionsResourceWithStreamingResponse:
        from .resources.transactions import TransactionsResourceWithStreamingResponse

        return TransactionsResourceWithStreamingResponse(self._client.transactions)

    @cached_property
    def budgets(self) -> budgets.BudgetsResourceWithStreamingResponse:
        from .resources.budgets import BudgetsResourceWithStreamingResponse

        return BudgetsResourceWithStreamingResponse(self._client.budgets)

    @cached_property
    def investments(self) -> investments.InvestmentsResourceWithStreamingResponse:
        from .resources.investments import InvestmentsResourceWithStreamingResponse

        return InvestmentsResourceWithStreamingResponse(self._client.investments)

    @cached_property
    def ai(self) -> ai.AIResourceWithStreamingResponse:
        from .resources.ai import AIResourceWithStreamingResponse

        return AIResourceWithStreamingResponse(self._client.ai)

    @cached_property
    def corporate(self) -> corporate.CorporateResourceWithStreamingResponse:
        from .resources.corporate import CorporateResourceWithStreamingResponse

        return CorporateResourceWithStreamingResponse(self._client.corporate)

    @cached_property
    def web3(self) -> web3.Web3ResourceWithStreamingResponse:
        from .resources.web3 import Web3ResourceWithStreamingResponse

        return Web3ResourceWithStreamingResponse(self._client.web3)

    @cached_property
    def payments(self) -> payments.PaymentsResourceWithStreamingResponse:
        from .resources.payments import PaymentsResourceWithStreamingResponse

        return PaymentsResourceWithStreamingResponse(self._client.payments)

    @cached_property
    def sustainability(self) -> sustainability.SustainabilityResourceWithStreamingResponse:
        from .resources.sustainability import SustainabilityResourceWithStreamingResponse

        return SustainabilityResourceWithStreamingResponse(self._client.sustainability)


class AsyncJocall3WithStreamedResponse:
    _client: AsyncJocall3

    def __init__(self, client: AsyncJocall3) -> None:
        self._client = client

    @cached_property
    def users(self) -> users.AsyncUsersResourceWithStreamingResponse:
        from .resources.users import AsyncUsersResourceWithStreamingResponse

        return AsyncUsersResourceWithStreamingResponse(self._client.users)

    @cached_property
    def accounts(self) -> accounts.AsyncAccountsResourceWithStreamingResponse:
        from .resources.accounts import AsyncAccountsResourceWithStreamingResponse

        return AsyncAccountsResourceWithStreamingResponse(self._client.accounts)

    @cached_property
    def transactions(self) -> transactions.AsyncTransactionsResourceWithStreamingResponse:
        from .resources.transactions import AsyncTransactionsResourceWithStreamingResponse

        return AsyncTransactionsResourceWithStreamingResponse(self._client.transactions)

    @cached_property
    def budgets(self) -> budgets.AsyncBudgetsResourceWithStreamingResponse:
        from .resources.budgets import AsyncBudgetsResourceWithStreamingResponse

        return AsyncBudgetsResourceWithStreamingResponse(self._client.budgets)

    @cached_property
    def investments(self) -> investments.AsyncInvestmentsResourceWithStreamingResponse:
        from .resources.investments import AsyncInvestmentsResourceWithStreamingResponse

        return AsyncInvestmentsResourceWithStreamingResponse(self._client.investments)

    @cached_property
    def ai(self) -> ai.AsyncAIResourceWithStreamingResponse:
        from .resources.ai import AsyncAIResourceWithStreamingResponse

        return AsyncAIResourceWithStreamingResponse(self._client.ai)

    @cached_property
    def corporate(self) -> corporate.AsyncCorporateResourceWithStreamingResponse:
        from .resources.corporate import AsyncCorporateResourceWithStreamingResponse

        return AsyncCorporateResourceWithStreamingResponse(self._client.corporate)

    @cached_property
    def web3(self) -> web3.AsyncWeb3ResourceWithStreamingResponse:
        from .resources.web3 import AsyncWeb3ResourceWithStreamingResponse

        return AsyncWeb3ResourceWithStreamingResponse(self._client.web3)

    @cached_property
    def payments(self) -> payments.AsyncPaymentsResourceWithStreamingResponse:
        from .resources.payments import AsyncPaymentsResourceWithStreamingResponse

        return AsyncPaymentsResourceWithStreamingResponse(self._client.payments)

    @cached_property
    def sustainability(self) -> sustainability.AsyncSustainabilityResourceWithStreamingResponse:
        from .resources.sustainability import AsyncSustainabilityResourceWithStreamingResponse

        return AsyncSustainabilityResourceWithStreamingResponse(self._client.sustainability)


Client = Jocall3

AsyncClient = AsyncJocall3
