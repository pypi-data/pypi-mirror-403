# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestAds:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_generate_video_ad(self, client: Jocall3) -> None:
        ad = client.ai.ads.generate_video_ad()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_generate_video_ad(self, client: Jocall3) -> None:
        response = client.ai.ads.with_raw_response.generate_video_ad()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_generate_video_ad(self, client: Jocall3) -> None:
        with client.ai.ads.with_streaming_response.generate_video_ad() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_get_generation_status(self, client: Jocall3) -> None:
        ad = client.ai.ads.get_generation_status(
            "op-video-gen-12345-abcde",
        )
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_get_generation_status(self, client: Jocall3) -> None:
        response = client.ai.ads.with_raw_response.get_generation_status(
            "op-video-gen-12345-abcde",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_get_generation_status(self, client: Jocall3) -> None:
        with client.ai.ads.with_streaming_response.get_generation_status(
            "op-video-gen-12345-abcde",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_get_generation_status(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `operation_id` but received ''"):
            client.ai.ads.with_raw_response.get_generation_status(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_generated_ads(self, client: Jocall3) -> None:
        ad = client.ai.ads.list_generated_ads()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_generated_ads_with_all_params(self, client: Jocall3) -> None:
        ad = client.ai.ads.list_generated_ads(
            limit=0,
            offset=0,
            status="status",
        )
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_generated_ads(self, client: Jocall3) -> None:
        response = client.ai.ads.with_raw_response.list_generated_ads()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_generated_ads(self, client: Jocall3) -> None:
        with client.ai.ads.with_streaming_response.list_generated_ads() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncAds:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_generate_video_ad(self, async_client: AsyncJocall3) -> None:
        ad = await async_client.ai.ads.generate_video_ad()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_generate_video_ad(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.ads.with_raw_response.generate_video_ad()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = await response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_generate_video_ad(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.ads.with_streaming_response.generate_video_ad() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = await response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_get_generation_status(self, async_client: AsyncJocall3) -> None:
        ad = await async_client.ai.ads.get_generation_status(
            "op-video-gen-12345-abcde",
        )
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_get_generation_status(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.ads.with_raw_response.get_generation_status(
            "op-video-gen-12345-abcde",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = await response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_get_generation_status(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.ads.with_streaming_response.get_generation_status(
            "op-video-gen-12345-abcde",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = await response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_get_generation_status(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `operation_id` but received ''"):
            await async_client.ai.ads.with_raw_response.get_generation_status(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_generated_ads(self, async_client: AsyncJocall3) -> None:
        ad = await async_client.ai.ads.list_generated_ads()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_generated_ads_with_all_params(self, async_client: AsyncJocall3) -> None:
        ad = await async_client.ai.ads.list_generated_ads(
            limit=0,
            offset=0,
            status="status",
        )
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_generated_ads(self, async_client: AsyncJocall3) -> None:
        response = await async_client.ai.ads.with_raw_response.list_generated_ads()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        ad = await response.parse()
        assert_matches_type(object, ad, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_generated_ads(self, async_client: AsyncJocall3) -> None:
        async with async_client.ai.ads.with_streaming_response.list_generated_ads() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            ad = await response.parse()
            assert_matches_type(object, ad, path=["response"])

        assert cast(Any, response.is_closed) is True
