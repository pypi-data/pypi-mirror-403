# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.payments import FxRetrieveRatesResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestFx:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_convert_currency(self, client: Jocall3) -> None:
        fx = client.payments.fx.convert_currency()
        assert_matches_type(object, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_convert_currency(self, client: Jocall3) -> None:
        response = client.payments.fx.with_raw_response.convert_currency()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = response.parse()
        assert_matches_type(object, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_convert_currency(self, client: Jocall3) -> None:
        with client.payments.fx.with_streaming_response.convert_currency() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = response.parse()
            assert_matches_type(object, fx, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_rates(self, client: Jocall3) -> None:
        fx = client.payments.fx.retrieve_rates()
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_rates_with_all_params(self, client: Jocall3) -> None:
        fx = client.payments.fx.retrieve_rates(
            base_currency="baseCurrency",
            forecast_days=0,
            target_currency="targetCurrency",
        )
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_rates(self, client: Jocall3) -> None:
        response = client.payments.fx.with_raw_response.retrieve_rates()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = response.parse()
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_rates(self, client: Jocall3) -> None:
        with client.payments.fx.with_streaming_response.retrieve_rates() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = response.parse()
            assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncFx:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_convert_currency(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.convert_currency()
        assert_matches_type(object, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_convert_currency(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.fx.with_raw_response.convert_currency()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = await response.parse()
        assert_matches_type(object, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_convert_currency(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.fx.with_streaming_response.convert_currency() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = await response.parse()
            assert_matches_type(object, fx, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_rates(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.retrieve_rates()
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_rates_with_all_params(self, async_client: AsyncJocall3) -> None:
        fx = await async_client.payments.fx.retrieve_rates(
            base_currency="baseCurrency",
            forecast_days=0,
            target_currency="targetCurrency",
        )
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_rates(self, async_client: AsyncJocall3) -> None:
        response = await async_client.payments.fx.with_raw_response.retrieve_rates()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        fx = await response.parse()
        assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_rates(self, async_client: AsyncJocall3) -> None:
        async with async_client.payments.fx.with_streaming_response.retrieve_rates() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            fx = await response.parse()
            assert_matches_type(FxRetrieveRatesResponse, fx, path=["response"])

        assert cast(Any, response.is_closed) is True
