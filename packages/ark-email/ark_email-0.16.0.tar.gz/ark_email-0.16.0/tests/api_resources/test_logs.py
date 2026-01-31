# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from ark import Ark, AsyncArk
from ark.types import LogEntry, LogRetrieveResponse
from ark._utils import parse_datetime
from tests.utils import assert_matches_type
from ark.pagination import SyncPageNumberPagination, AsyncPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestLogs:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: Ark) -> None:
        log = client.logs.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        )
        assert_matches_type(LogRetrieveResponse, log, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Ark) -> None:
        response = client.logs.with_raw_response.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        log = response.parse()
        assert_matches_type(LogRetrieveResponse, log, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Ark) -> None:
        with client.logs.with_streaming_response.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            log = response.parse()
            assert_matches_type(LogRetrieveResponse, log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `request_id` but received ''"):
            client.logs.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_list(self, client: Ark) -> None:
        log = client.logs.list()
        assert_matches_type(SyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Ark) -> None:
        log = client.logs.list(
            credential_id="credentialId",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            endpoint="endpoint",
            page=1,
            per_page=1,
            request_id="requestId",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            status="success",
            status_code=100,
        )
        assert_matches_type(SyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Ark) -> None:
        response = client.logs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        log = response.parse()
        assert_matches_type(SyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Ark) -> None:
        with client.logs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            log = response.parse()
            assert_matches_type(SyncPageNumberPagination[LogEntry], log, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncLogs:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArk) -> None:
        log = await async_client.logs.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        )
        assert_matches_type(LogRetrieveResponse, log, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArk) -> None:
        response = await async_client.logs.with_raw_response.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        log = await response.parse()
        assert_matches_type(LogRetrieveResponse, log, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArk) -> None:
        async with async_client.logs.with_streaming_response.retrieve(
            "req_V8GGcdWYzgeWIHiI",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            log = await response.parse()
            assert_matches_type(LogRetrieveResponse, log, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `request_id` but received ''"):
            await async_client.logs.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncArk) -> None:
        log = await async_client.logs.list()
        assert_matches_type(AsyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncArk) -> None:
        log = await async_client.logs.list(
            credential_id="credentialId",
            end_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            endpoint="endpoint",
            page=1,
            per_page=1,
            request_id="requestId",
            start_date=parse_datetime("2019-12-27T18:11:19.117Z"),
            status="success",
            status_code=100,
        )
        assert_matches_type(AsyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncArk) -> None:
        response = await async_client.logs.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        log = await response.parse()
        assert_matches_type(AsyncPageNumberPagination[LogEntry], log, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncArk) -> None:
        async with async_client.logs.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            log = await response.parse()
            assert_matches_type(AsyncPageNumberPagination[LogEntry], log, path=["response"])

        assert cast(Any, response.is_closed) is True
