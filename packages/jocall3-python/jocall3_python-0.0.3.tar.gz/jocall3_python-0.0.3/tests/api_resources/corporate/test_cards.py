# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types.corporate import (
    CardFreezeResponse,
    CardCreateVirtualResponse,
    CardUpdateControlsResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestCards:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        card = client.corporate.cards.list()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Jocall3) -> None:
        card = client.corporate.cards.list(
            limit=0,
            offset=0,
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.corporate.cards.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = response.parse()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.corporate.cards.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = response.parse()
            assert_matches_type(object, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_create_virtual(self, client: Jocall3) -> None:
        card = client.corporate.cards.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        )
        assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_create_virtual(self, client: Jocall3) -> None:
        response = client.corporate.cards.with_raw_response.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = response.parse()
        assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_create_virtual(self, client: Jocall3) -> None:
        with client.corporate.cards.with_streaming_response.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = response.parse()
            assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_freeze(self, client: Jocall3) -> None:
        card = client.corporate.cards.freeze(
            "corp_card_xyz987654",
        )
        assert_matches_type(CardFreezeResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_freeze(self, client: Jocall3) -> None:
        response = client.corporate.cards.with_raw_response.freeze(
            "corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = response.parse()
        assert_matches_type(CardFreezeResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_freeze(self, client: Jocall3) -> None:
        with client.corporate.cards.with_streaming_response.freeze(
            "corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = response.parse()
            assert_matches_type(CardFreezeResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_freeze(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            client.corporate.cards.with_raw_response.freeze(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_transactions(self, client: Jocall3) -> None:
        card = client.corporate.cards.list_transactions(
            card_id="corp_card_xyz987654",
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_transactions_with_all_params(self, client: Jocall3) -> None:
        card = client.corporate.cards.list_transactions(
            card_id="corp_card_xyz987654",
            end_date="endDate",
            limit=0,
            offset=0,
            start_date="startDate",
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_transactions(self, client: Jocall3) -> None:
        response = client.corporate.cards.with_raw_response.list_transactions(
            card_id="corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = response.parse()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_transactions(self, client: Jocall3) -> None:
        with client.corporate.cards.with_streaming_response.list_transactions(
            card_id="corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = response.parse()
            assert_matches_type(object, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_list_transactions(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            client.corporate.cards.with_raw_response.list_transactions(
                card_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_controls(self, client: Jocall3) -> None:
        card = client.corporate.cards.update_controls(
            "corp_card_xyz987654",
        )
        assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_controls(self, client: Jocall3) -> None:
        response = client.corporate.cards.with_raw_response.update_controls(
            "corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = response.parse()
        assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_controls(self, client: Jocall3) -> None:
        with client.corporate.cards.with_streaming_response.update_controls(
            "corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = response.parse()
            assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_controls(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            client.corporate.cards.with_raw_response.update_controls(
                "",
            )


class TestAsyncCards:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.list()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.list(
            limit=0,
            offset=0,
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.cards.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = await response.parse()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.cards.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = await response.parse()
            assert_matches_type(object, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_create_virtual(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        )
        assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_create_virtual(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.cards.with_raw_response.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = await response.parse()
        assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_create_virtual(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.cards.with_streaming_response.create_virtual(
            controls={
                "atmWithdrawals": False,
                "contactlessPayments": False,
                "onlineTransactions": True,
                "internationalTransactions": False,
                "monthlyLimit": 1000,
                "dailyLimit": 500,
                "singleTransactionLimit": 200,
                "merchantCategoryRestrictions": ["Advertising"],
                "vendorRestrictions": ["Facebook Ads", "Google Ads"],
            },
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = await response.parse()
            assert_matches_type(CardCreateVirtualResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_freeze(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.freeze(
            "corp_card_xyz987654",
        )
        assert_matches_type(CardFreezeResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_freeze(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.cards.with_raw_response.freeze(
            "corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = await response.parse()
        assert_matches_type(CardFreezeResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_freeze(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.cards.with_streaming_response.freeze(
            "corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = await response.parse()
            assert_matches_type(CardFreezeResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_freeze(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            await async_client.corporate.cards.with_raw_response.freeze(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_transactions(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.list_transactions(
            card_id="corp_card_xyz987654",
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_transactions_with_all_params(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.list_transactions(
            card_id="corp_card_xyz987654",
            end_date="endDate",
            limit=0,
            offset=0,
            start_date="startDate",
        )
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_transactions(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.cards.with_raw_response.list_transactions(
            card_id="corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = await response.parse()
        assert_matches_type(object, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_transactions(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.cards.with_streaming_response.list_transactions(
            card_id="corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = await response.parse()
            assert_matches_type(object, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_list_transactions(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            await async_client.corporate.cards.with_raw_response.list_transactions(
                card_id="",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_controls(self, async_client: AsyncJocall3) -> None:
        card = await async_client.corporate.cards.update_controls(
            "corp_card_xyz987654",
        )
        assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_controls(self, async_client: AsyncJocall3) -> None:
        response = await async_client.corporate.cards.with_raw_response.update_controls(
            "corp_card_xyz987654",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        card = await response.parse()
        assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_controls(self, async_client: AsyncJocall3) -> None:
        async with async_client.corporate.cards.with_streaming_response.update_controls(
            "corp_card_xyz987654",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            card = await response.parse()
            assert_matches_type(CardUpdateControlsResponse, card, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_controls(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `card_id` but received ''"):
            await async_client.corporate.cards.with_raw_response.update_controls(
                "",
            )
