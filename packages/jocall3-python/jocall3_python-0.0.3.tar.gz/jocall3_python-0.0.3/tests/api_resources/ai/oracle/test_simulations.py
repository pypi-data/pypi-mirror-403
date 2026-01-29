# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.ai.oracle import SimulationRetrieveResultsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSimulations:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_all(self, client: Jocall3) -> None:
        simulation = client.ai.oracle.simulations.list_all()
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_all_with_all_params(self, client: Jocall3) -> None:
        simulation = client.ai.oracle.simulations.list_all(
            limit=0,
            offset=0,
        )
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_all(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulations.with_raw_response.list_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulation = response.parse()
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_all(self, client: Jocall3) -> None:
        with client.ai.oracle.simulations.with_streaming_response.list_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulation = response.parse()
            assert_matches_type(object, simulation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_results(self, client: Jocall3) -> None:
        simulation = client.ai.oracle.simulations.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        )
        assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_results(self, client: Jocall3) -> None:
        response = client.ai.oracle.simulations.with_raw_response.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulation = response.parse()
        assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_results(self, client: Jocall3) -> None:
        with client.ai.oracle.simulations.with_streaming_response.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulation = response.parse()
            assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve_results(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `simulation_id` but received ''"):
            client.ai.oracle.simulations.with_raw_response.retrieve_results(
                "",
            )


class TestAsyncSimulations:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_all(self, async_client: AsyncJocall3) -> None:
        simulation = await async_client.ai.oracle.simulations.list_all()
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_all_with_all_params(self, async_client: AsyncJocall3) -> None:
        simulation = await async_client.ai.oracle.simulations.list_all(
            limit=0,
            offset=0,
        )
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_all(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulations.with_raw_response.list_all()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulation = await response.parse()
        assert_matches_type(object, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_all(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulations.with_streaming_response.list_all() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulation = await response.parse()
            assert_matches_type(object, simulation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_results(self, async_client: AsyncJocall3) -> None:
        simulation = await async_client.ai.oracle.simulations.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        )
        assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_results(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.oracle.simulations.with_raw_response.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        simulation = await response.parse()
        assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_results(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.oracle.simulations.with_streaming_response.retrieve_results(
            "sim_oracle-growth-2024-xyz",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            simulation = await response.parse()
            assert_matches_type(SimulationRetrieveResultsResponse, simulation, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve_results(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `simulation_id` but received ''"):
            await async_client.ai.oracle.simulations.with_raw_response.retrieve_results(
                "",
            )
