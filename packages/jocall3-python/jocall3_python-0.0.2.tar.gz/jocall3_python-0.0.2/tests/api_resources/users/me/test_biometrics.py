# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.users.me import BiometricVerifyResponse, BiometricRetrieveStatusResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestBiometrics:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve_status(self, client: Jocall3) -> None:
        biometric = client.users.me.biometrics.retrieve_status()
        assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve_status(self, client: Jocall3) -> None:
        response = client.users.me.biometrics.with_raw_response.retrieve_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        biometric = response.parse()
        assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve_status(self, client: Jocall3) -> None:
        with client.users.me.biometrics.with_streaming_response.retrieve_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            biometric = response.parse()
            assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_verify(self, client: Jocall3) -> None:
        biometric = client.users.me.biometrics.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        )
        assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_verify(self, client: Jocall3) -> None:
        response = client.users.me.biometrics.with_raw_response.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        biometric = response.parse()
        assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_verify(self, client: Jocall3) -> None:
        with client.users.me.biometrics.with_streaming_response.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            biometric = response.parse()
            assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncBiometrics:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve_status(self, async_client: AsyncJocall3) -> None:
        biometric = await async_client.users.me.biometrics.retrieve_status()
        assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.biometrics.with_raw_response.retrieve_status()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        biometric = await response.parse()
        assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.biometrics.with_streaming_response.retrieve_status() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            biometric = await response.parse()
            assert_matches_type(BiometricRetrieveStatusResponse, biometric, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_verify(self, async_client: AsyncJocall3) -> None:
        biometric = await async_client.users.me.biometrics.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        )
        assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_verify(self, async_client: AsyncJocall3) -> None:
        response = await async_client.users.me.biometrics.with_raw_response.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        biometric = await response.parse()
        assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_verify(self, async_client: AsyncJocall3) -> None:
        async with async_client.users.me.biometrics.with_streaming_response.verify(
            biometric_signature="base64encoded_one_time_fingerprint_proof",
            biometric_type="fingerprint",
            device_id="dev_mobile_android_ddeeff",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            biometric = await response.parse()
            assert_matches_type(BiometricVerifyResponse, biometric, path=["response"])

        assert cast(Any, response.is_closed) is True
