# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from ark import Ark, AsyncArk
from ark.types import (
    SuppressionListResponse,
    SuppressionCreateResponse,
    SuppressionDeleteResponse,
    SuppressionRetrieveResponse,
    SuppressionBulkCreateResponse,
)
from tests.utils import assert_matches_type
from ark.pagination import SyncPageNumberPagination, AsyncPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestSuppressions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Ark) -> None:
        suppression = client.suppressions.create(
            address="user@example.com",
        )
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Ark) -> None:
        suppression = client.suppressions.create(
            address="user@example.com",
            reason="user requested removal",
        )
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Ark) -> None:
        response = client.suppressions.with_raw_response.create(
            address="user@example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = response.parse()
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Ark) -> None:
        with client.suppressions.with_streaming_response.create(
            address="user@example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = response.parse()
            assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: Ark) -> None:
        suppression = client.suppressions.retrieve(
            "dev@stainless.com",
        )
        assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Ark) -> None:
        response = client.suppressions.with_raw_response.retrieve(
            "dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = response.parse()
        assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Ark) -> None:
        with client.suppressions.with_streaming_response.retrieve(
            "dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = response.parse()
            assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email` but received ''"):
            client.suppressions.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_list(self, client: Ark) -> None:
        suppression = client.suppressions.list()
        assert_matches_type(SyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Ark) -> None:
        suppression = client.suppressions.list(
            page=0,
            per_page=100,
        )
        assert_matches_type(SyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Ark) -> None:
        response = client.suppressions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = response.parse()
        assert_matches_type(SyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Ark) -> None:
        with client.suppressions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = response.parse()
            assert_matches_type(SyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: Ark) -> None:
        suppression = client.suppressions.delete(
            "dev@stainless.com",
        )
        assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Ark) -> None:
        response = client.suppressions.with_raw_response.delete(
            "dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = response.parse()
        assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Ark) -> None:
        with client.suppressions.with_streaming_response.delete(
            "dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = response.parse()
            assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email` but received ''"):
            client.suppressions.with_raw_response.delete(
                "",
            )

    @parametrize
    def test_method_bulk_create(self, client: Ark) -> None:
        suppression = client.suppressions.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        )
        assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

    @parametrize
    def test_raw_response_bulk_create(self, client: Ark) -> None:
        response = client.suppressions.with_raw_response.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = response.parse()
        assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

    @parametrize
    def test_streaming_response_bulk_create(self, client: Ark) -> None:
        with client.suppressions.with_streaming_response.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = response.parse()
            assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncSuppressions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.create(
            address="user@example.com",
        )
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.create(
            address="user@example.com",
            reason="user requested removal",
        )
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncArk) -> None:
        response = await async_client.suppressions.with_raw_response.create(
            address="user@example.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = await response.parse()
        assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncArk) -> None:
        async with async_client.suppressions.with_streaming_response.create(
            address="user@example.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = await response.parse()
            assert_matches_type(SuppressionCreateResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.retrieve(
            "dev@stainless.com",
        )
        assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArk) -> None:
        response = await async_client.suppressions.with_raw_response.retrieve(
            "dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = await response.parse()
        assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArk) -> None:
        async with async_client.suppressions.with_streaming_response.retrieve(
            "dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = await response.parse()
            assert_matches_type(SuppressionRetrieveResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email` but received ''"):
            await async_client.suppressions.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.list()
        assert_matches_type(AsyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.list(
            page=0,
            per_page=100,
        )
        assert_matches_type(AsyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncArk) -> None:
        response = await async_client.suppressions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = await response.parse()
        assert_matches_type(AsyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncArk) -> None:
        async with async_client.suppressions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = await response.parse()
            assert_matches_type(AsyncPageNumberPagination[SuppressionListResponse], suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.delete(
            "dev@stainless.com",
        )
        assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArk) -> None:
        response = await async_client.suppressions.with_raw_response.delete(
            "dev@stainless.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = await response.parse()
        assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArk) -> None:
        async with async_client.suppressions.with_streaming_response.delete(
            "dev@stainless.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = await response.parse()
            assert_matches_type(SuppressionDeleteResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email` but received ''"):
            await async_client.suppressions.with_raw_response.delete(
                "",
            )

    @parametrize
    async def test_method_bulk_create(self, async_client: AsyncArk) -> None:
        suppression = await async_client.suppressions.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        )
        assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

    @parametrize
    async def test_raw_response_bulk_create(self, async_client: AsyncArk) -> None:
        response = await async_client.suppressions.with_raw_response.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        suppression = await response.parse()
        assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

    @parametrize
    async def test_streaming_response_bulk_create(self, async_client: AsyncArk) -> None:
        async with async_client.suppressions.with_streaming_response.bulk_create(
            suppressions=[{"address": "dev@stainless.com"}],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            suppression = await response.parse()
            assert_matches_type(SuppressionBulkCreateResponse, suppression, path=["response"])

        assert cast(Any, response.is_closed) is True
