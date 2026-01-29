# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from jocall3 import Jocall3, AsyncJocall3
from tests.utils import assert_matches_type
from jocall3.types import (
    TransactionListResponse,
    TransactionRetrieveResponse,
    TransactionCategorizeResponse,
    TransactionUpdateNotesResponse,
    TransactionListRecurringResponse,
)

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTransactions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_retrieve(self, client: Jocall3) -> None:
        transaction = client.transactions.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        )
        assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_retrieve(self, client: Jocall3) -> None:
        response = client.transactions.with_raw_response.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_retrieve(self, client: Jocall3) -> None:
        with client.transactions.with_streaming_response.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_retrieve(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            client.transactions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list(self, client: Jocall3) -> None:
        transaction = client.transactions.list()
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_with_all_params(self, client: Jocall3) -> None:
        transaction = client.transactions.list(
            category="category",
            end_date="endDate",
            limit=0,
            max_amount=0,
            min_amount=0,
            offset=0,
            search_query="searchQuery",
            start_date="startDate",
            type="type",
        )
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list(self, client: Jocall3) -> None:
        response = client.transactions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list(self, client: Jocall3) -> None:
        with client.transactions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionListResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_categorize(self, client: Jocall3) -> None:
        transaction = client.transactions.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        )
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_categorize_with_all_params(self, client: Jocall3) -> None:
        transaction = client.transactions.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
            apply_to_future=True,
            notes="Bulk purchase for party",
        )
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_categorize(self, client: Jocall3) -> None:
        response = client.transactions.with_raw_response.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_categorize(self, client: Jocall3) -> None:
        with client.transactions.with_streaming_response.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_categorize(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            client.transactions.with_raw_response.categorize(
                transaction_id="",
                category="Home > Groceries",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_recurring(self, client: Jocall3) -> None:
        transaction = client.transactions.list_recurring()
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_list_recurring_with_all_params(self, client: Jocall3) -> None:
        transaction = client.transactions.list_recurring(
            limit=0,
            offset=0,
        )
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_list_recurring(self, client: Jocall3) -> None:
        response = client.transactions.with_raw_response.list_recurring()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_list_recurring(self, client: Jocall3) -> None:
        with client.transactions.with_streaming_response.list_recurring() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_method_update_notes(self, client: Jocall3) -> None:
        transaction = client.transactions.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        )
        assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_raw_response_update_notes(self, client: Jocall3) -> None:
        response = client.transactions.with_raw_response.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = response.parse()
        assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_streaming_response_update_notes(self, client: Jocall3) -> None:
        with client.transactions.with_streaming_response.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = response.parse()
            assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    def test_path_params_update_notes(self, client: Jocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            client.transactions.with_raw_response.update_notes(
                transaction_id="",
                notes="This was a special coffee for a client meeting.",
            )


class TestAsyncTransactions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        )
        assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.with_raw_response.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.with_streaming_response.retrieve(
            "txn_quantum-2024-07-21-A7B8C9",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionRetrieveResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            await async_client.transactions.with_raw_response.retrieve(
                "",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.list()
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.list(
            category="category",
            end_date="endDate",
            limit=0,
            max_amount=0,
            min_amount=0,
            offset=0,
            search_query="searchQuery",
            start_date="startDate",
            type="type",
        )
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionListResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionListResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_categorize(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        )
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_categorize_with_all_params(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
            apply_to_future=True,
            notes="Bulk purchase for party",
        )
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_categorize(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.with_raw_response.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_categorize(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.with_streaming_response.categorize(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            category="Home > Groceries",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionCategorizeResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_categorize(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            await async_client.transactions.with_raw_response.categorize(
                transaction_id="",
                category="Home > Groceries",
            )

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_recurring(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.list_recurring()
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_list_recurring_with_all_params(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.list_recurring(
            limit=0,
            offset=0,
        )
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_list_recurring(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.with_raw_response.list_recurring()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_list_recurring(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.with_streaming_response.list_recurring() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionListRecurringResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_method_update_notes(self, async_client: AsyncJocall3) -> None:
        transaction = await async_client.transactions.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        )
        assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_raw_response_update_notes(self, async_client: AsyncJocall3) -> None:
        response = await async_client.transactions.with_raw_response.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        transaction = await response.parse()
        assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_streaming_response_update_notes(self, async_client: AsyncJocall3) -> None:
        async with async_client.transactions.with_streaming_response.update_notes(
            transaction_id="txn_quantum-2024-07-21-A7B8C9",
            notes="This was a special coffee for a client meeting.",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            transaction = await response.parse()
            assert_matches_type(TransactionUpdateNotesResponse, transaction, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip(reason="Prism tests are disabled")
    @parametrize
    async def test_path_params_update_notes(self, async_client: AsyncJocall3) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `transaction_id` but received ''"):
            await async_client.transactions.with_raw_response.update_notes(
                transaction_id="",
                notes="This was a special coffee for a client meeting.",
            )
