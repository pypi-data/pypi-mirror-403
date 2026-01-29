# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.users import (
    PasswordResetConfirmResponse,
    PasswordResetInitiateResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestPasswordReset:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_confirm(self, client: Jocall3) -> None:
        password_reset = client.users.password_reset.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        )
        assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_confirm(self, client: Jocall3) -> None:
        response = client.users.password_reset.with_raw_response.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        password_reset = response.parse()
        assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_confirm(self, client: Jocall3) -> None:
        with client.users.password_reset.with_streaming_response.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            password_reset = response.parse()
            assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_initiate(self, client: Jocall3) -> None:
        password_reset = client.users.password_reset.initiate(
            identifier="reset.user@example.com",
        )
        assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_initiate(self, client: Jocall3) -> None:
        response = client.users.password_reset.with_raw_response.initiate(
            identifier="reset.user@example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        password_reset = response.parse()
        assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_initiate(self, client: Jocall3) -> None:
        with client.users.password_reset.with_streaming_response.initiate(
            identifier="reset.user@example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            password_reset = response.parse()
            assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncPasswordReset:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_confirm(self, async_client: AsyncJocall3) -> None:
        password_reset = await async_client.users.password_reset.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        )
        assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_confirm(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.password_reset.with_raw_response.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        password_reset = await response.parse()
        assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_confirm(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.password_reset.with_streaming_response.confirm(
            identifier="reset.user@example.com",
            new_password="MyNewStrongPassword@789",
            verification_code="654321",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            password_reset = await response.parse()
            assert_matches_type(PasswordResetConfirmResponse, password_reset, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_initiate(self, async_client: AsyncJocall3) -> None:
        password_reset = await async_client.users.password_reset.initiate(
            identifier="reset.user@example.com",
        )
        assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_initiate(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.password_reset.with_raw_response.initiate(
            identifier="reset.user@example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        password_reset = await response.parse()
        assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_initiate(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.password_reset.with_streaming_response.initiate(
            identifier="reset.user@example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            password_reset = await response.parse()
            assert_matches_type(PasswordResetInitiateResponse, password_reset, path=["response"])

        assert cast(Any, response.is_closed) is True
