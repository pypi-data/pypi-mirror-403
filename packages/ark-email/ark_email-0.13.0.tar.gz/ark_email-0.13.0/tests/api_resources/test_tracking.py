# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from ark import Ark, AsyncArk
from ark.types import (
    TrackingListResponse,
    TrackingCreateResponse,
    TrackingDeleteResponse,
    TrackingUpdateResponse,
    TrackingVerifyResponse,
    TrackingRetrieveResponse,
)
from tests.utils import assert_matches_type

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestTracking:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_create(self, client: Ark) -> None:
        tracking = client.tracking.create(
            domain_id=123,
            name="track",
        )
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    def test_method_create_with_all_params(self, client: Ark) -> None:
        tracking = client.tracking.create(
            domain_id=123,
            name="track",
            ssl_enabled=True,
            track_clicks=True,
            track_opens=True,
        )
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_create(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.create(
            domain_id=123,
            name="track",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_create(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.create(
            domain_id=123,
            name="track",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve(self, client: Ark) -> None:
        tracking = client.tracking.retrieve(
            "trackingId",
        )
        assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.retrieve(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.retrieve(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            client.tracking.with_raw_response.retrieve(
                "",
            )

    @parametrize
    def test_method_update(self, client: Ark) -> None:
        tracking = client.tracking.update(
            tracking_id="trackingId",
        )
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    def test_method_update_with_all_params(self, client: Ark) -> None:
        tracking = client.tracking.update(
            tracking_id="trackingId",
            excluded_click_domains="example.com,mysite.org",
            ssl_enabled=True,
            track_clicks=True,
            track_opens=True,
        )
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_update(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.update(
            tracking_id="trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_update(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.update(
            tracking_id="trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_update(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            client.tracking.with_raw_response.update(
                tracking_id="",
            )

    @parametrize
    def test_method_list(self, client: Ark) -> None:
        tracking = client.tracking.list()
        assert_matches_type(TrackingListResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingListResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingListResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_delete(self, client: Ark) -> None:
        tracking = client.tracking.delete(
            "trackingId",
        )
        assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_delete(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.delete(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_delete(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.delete(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_delete(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            client.tracking.with_raw_response.delete(
                "",
            )

    @parametrize
    def test_method_verify(self, client: Ark) -> None:
        tracking = client.tracking.verify(
            "trackingId",
        )
        assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

    @parametrize
    def test_raw_response_verify(self, client: Ark) -> None:
        response = client.tracking.with_raw_response.verify(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = response.parse()
        assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

    @parametrize
    def test_streaming_response_verify(self, client: Ark) -> None:
        with client.tracking.with_streaming_response.verify(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = response.parse()
            assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_verify(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            client.tracking.with_raw_response.verify(
                "",
            )


class TestAsyncTracking:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_create(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.create(
            domain_id=123,
            name="track",
        )
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.create(
            domain_id=123,
            name="track",
            ssl_enabled=True,
            track_clicks=True,
            track_opens=True,
        )
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_create(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.create(
            domain_id=123,
            name="track",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.create(
            domain_id=123,
            name="track",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingCreateResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.retrieve(
            "trackingId",
        )
        assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.retrieve(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.retrieve(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingRetrieveResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            await async_client.tracking.with_raw_response.retrieve(
                "",
            )

    @parametrize
    async def test_method_update(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.update(
            tracking_id="trackingId",
        )
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    async def test_method_update_with_all_params(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.update(
            tracking_id="trackingId",
            excluded_click_domains="example.com,mysite.org",
            ssl_enabled=True,
            track_clicks=True,
            track_opens=True,
        )
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_update(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.update(
            tracking_id="trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_update(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.update(
            tracking_id="trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingUpdateResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_update(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            await async_client.tracking.with_raw_response.update(
                tracking_id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.list()
        assert_matches_type(TrackingListResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingListResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingListResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_delete(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.delete(
            "trackingId",
        )
        assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_delete(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.delete(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_delete(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.delete(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingDeleteResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_delete(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            await async_client.tracking.with_raw_response.delete(
                "",
            )

    @parametrize
    async def test_method_verify(self, async_client: AsyncArk) -> None:
        tracking = await async_client.tracking.verify(
            "trackingId",
        )
        assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

    @parametrize
    async def test_raw_response_verify(self, async_client: AsyncArk) -> None:
        response = await async_client.tracking.with_raw_response.verify(
            "trackingId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        tracking = await response.parse()
        assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

    @parametrize
    async def test_streaming_response_verify(self, async_client: AsyncArk) -> None:
        async with async_client.tracking.with_streaming_response.verify(
            "trackingId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            tracking = await response.parse()
            assert_matches_type(TrackingVerifyResponse, tracking, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_verify(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `tracking_id` but received ''"):
            await async_client.tracking.with_raw_response.verify(
                "",
            )
