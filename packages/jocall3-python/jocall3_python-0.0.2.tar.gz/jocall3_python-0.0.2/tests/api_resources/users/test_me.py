# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.users import (
    MeUpdateResponse,
    MeRetrieveResponse,
    MeListDevicesResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMe:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Jocall3) -> None:
        me = client.users.me.retrieve()
        assert_matches_type(MeRetrieveResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Jocall3) -> None:
        response = client.users.me.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = response.parse()
        assert_matches_type(MeRetrieveResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Jocall3) -> None:
        with client.users.me.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = response.parse()
            assert_matches_type(MeRetrieveResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update(self, client: Jocall3) -> None:
        me = client.users.me.update()
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_with_all_params(self, client: Jocall3) -> None:
        me = client.users.me.update(
            address={
                "city": "city",
                "country": "country",
                "state": "state",
                "street": "street",
                "zip": "zip",
            },
            name="Quantum Visionary Pro",
            phone="+1-555-999-0000",
            preferences={
                "ai_interaction_mode": "aiInteractionMode",
                "data_sharing_consent": True,
                "notification_channels": {
                    "email": True,
                    "in_app": True,
                    "push": True,
                    "sms": True,
                },
                "preferred_language": "preferredLanguage",
                "theme": "theme",
                "transaction_grouping": "transactionGrouping",
            },
        )
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update(self, client: Jocall3) -> None:
        response = client.users.me.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = response.parse()
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update(self, client: Jocall3) -> None:
        with client.users.me.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = response.parse()
            assert_matches_type(MeUpdateResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_devices(self, client: Jocall3) -> None:
        me = client.users.me.list_devices()
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_devices_with_all_params(self, client: Jocall3) -> None:
        me = client.users.me.list_devices(
            limit=0,
            offset=0,
        )
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_devices(self, client: Jocall3) -> None:
        response = client.users.me.with_raw_response.list_devices()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = response.parse()
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_devices(self, client: Jocall3) -> None:
        with client.users.me.with_streaming_response.list_devices() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = response.parse()
            assert_matches_type(MeListDevicesResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMe:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncJocall3) -> None:
        me = await async_client.users.me.retrieve()
        assert_matches_type(MeRetrieveResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = await response.parse()
        assert_matches_type(MeRetrieveResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = await response.parse()
            assert_matches_type(MeRetrieveResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update(self, async_client: AsyncJocall3) -> None:
        me = await async_client.users.me.update()
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncJocall3) -> None:
        me = await async_client.users.me.update(
            address={
                "city": "city",
                "country": "country",
                "state": "state",
                "street": "street",
                "zip": "zip",
            },
            name="Quantum Visionary Pro",
            phone="+1-555-999-0000",
            preferences={
                "ai_interaction_mode": "aiInteractionMode",
                "data_sharing_consent": True,
                "notification_channels": {
                    "email": True,
                    "in_app": True,
                    "push": True,
                    "sms": True,
                },
                "preferred_language": "preferredLanguage",
                "theme": "theme",
                "transaction_grouping": "transactionGrouping",
            },
        )
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.with_raw_response.update()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = await response.parse()
        assert_matches_type(MeUpdateResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.with_streaming_response.update() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = await response.parse()
            assert_matches_type(MeUpdateResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_devices(self, async_client: AsyncJocall3) -> None:
        me = await async_client.users.me.list_devices()
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_devices_with_all_params(self, async_client: AsyncJocall3) -> None:
        me = await async_client.users.me.list_devices(
            limit=0,
            offset=0,
        )
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_devices(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.with_raw_response.list_devices()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        me = await response.parse()
        assert_matches_type(MeListDevicesResponse, me, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_devices(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.with_streaming_response.list_devices() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            me = await response.parse()
            assert_matches_type(MeListDevicesResponse, me, path=["response"])

        assert cast(Any, response.is_closed) is True
