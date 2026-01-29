# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types import UserLoginResponse, UserRegisterResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUsers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_login(self, client: Jocall3) -> None:
        user = client.users.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_login(self, client: Jocall3) -> None:
        response = client.users.with_raw_response.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_login(self, client: Jocall3) -> None:
        with client.users.with_streaming_response.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserLoginResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register(self, client: Jocall3) -> None:
        user = client.users.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        )
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_register_with_all_params(self, client: Jocall3) -> None:
        user = client.users.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
            address={
                "city": "city",
                "country": "country",
                "state": "state",
                "street": "street",
                "zip": "zip",
            },
            phone="+1-555-987-6543",
        )
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_register(self, client: Jocall3) -> None:
        response = client.users.with_raw_response.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_register(self, client: Jocall3) -> None:
        with client.users.with_streaming_response.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserRegisterResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncUsers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_login(self, async_client: AsyncJocall3) -> None:
        user = await async_client.users.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        )
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_login(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.with_raw_response.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserLoginResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_login(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.with_streaming_response.login(
            email="quantum.visionary@demobank.com",
            password="YourSecurePassword123",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserLoginResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register(self, async_client: AsyncJocall3) -> None:
        user = await async_client.users.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        )
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_register_with_all_params(self, async_client: AsyncJocall3) -> None:
        user = await async_client.users.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
            address={
                "city": "city",
                "country": "country",
                "state": "state",
                "street": "street",
                "zip": "zip",
            },
            phone="+1-555-987-6543",
        )
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_register(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.with_raw_response.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserRegisterResponse, user, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_register(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.with_streaming_response.register(
            email="alice.w@example.com",
            name="Alice Wonderland",
            password="SecureP@ssw0rd2024!",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserRegisterResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True
