# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.ai.oracle import SimulateRunStandardSimulationResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSimulate:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_advanced_simulation(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.run_advanced_simulation()
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_advanced_simulation_with_all_params(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.run_advanced_simulation(
            global_economic_factors={},
            personal_assumptions={},
        )
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run_advanced_simulation(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulate.with_raw_response.run_advanced_simulation()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = response.parse()
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run_advanced_simulation(self, client: Jocall3) -> None:
        with client.ai.oracle.simulate.with_streaming_response.run_advanced_simulation() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = response.parse()
            assert_matches_type(object, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_run_standard_simulation(self, client: Jocall3) -> None:
        simulate = client.ai.oracle.simulate.run_standard_simulation()
        assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_run_standard_simulation(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulate.with_raw_response.run_standard_simulation()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = response.parse()
        assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_run_standard_simulation(self, client: Jocall3) -> None:
        with client.ai.oracle.simulate.with_streaming_response.run_standard_simulation() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = response.parse()
            assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSimulate:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run_advanced_simulation(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.run_advanced_simulation()
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run_advanced_simulation_with_all_params(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.run_advanced_simulation(
            global_economic_factors={},
            personal_assumptions={},
        )
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run_advanced_simulation(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulate.with_raw_response.run_advanced_simulation()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = await response.parse()
        assert_matches_type(object, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run_advanced_simulation(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulate.with_streaming_response.run_advanced_simulation() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = await response.parse()
            assert_matches_type(object, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_run_standard_simulation(self, async_client: AsyncJocall3) -> None:
        simulate = await async_client.ai.oracle.simulate.run_standard_simulation()
        assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_run_standard_simulation(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulate.with_raw_response.run_standard_simulation()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulate = await response.parse()
        assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_run_standard_simulation(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulate.with_streaming_response.run_standard_simulation() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulate = await response.parse()
            assert_matches_type(SimulateRunStandardSimulationResponse, simulate, path=["response"])

        assert cast(Any, response.is_closed) is True
