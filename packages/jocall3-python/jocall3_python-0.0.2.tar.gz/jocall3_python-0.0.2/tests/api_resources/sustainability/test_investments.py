# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.sustainability import InvestmentAnalyzeImpactResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestInvestments:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_analyze_impact(self, client: Jocall3) -> None:
        investment = client.sustainability.investments.analyze_impact()
        assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_analyze_impact(self, client: Jocall3) -> None:
        response = client.sustainability.investments.with_raw_response.analyze_impact()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        investment = response.parse()
        assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_analyze_impact(self, client: Jocall3) -> None:
        with client.sustainability.investments.with_streaming_response.analyze_impact() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            investment = response.parse()
            assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncInvestments:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_analyze_impact(self, async_client: AsyncJocall3) -> None:
        investment = await async_client.sustainability.investments.analyze_impact()
        assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_analyze_impact(self, async_client: AsyncJocall3) -> None:
        response = await async_client.sustainability.investments.with_raw_response.analyze_impact()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        investment = await response.parse()
        assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_analyze_impact(self, async_client: AsyncJocall3) -> None:
        async with async_client.sustainability.investments.with_streaming_response.analyze_impact() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            investment = await response.parse()
            assert_matches_type(InvestmentAnalyzeImpactResponse, investment, path=["response"])

        assert cast(Any, response.is_closed) is True
