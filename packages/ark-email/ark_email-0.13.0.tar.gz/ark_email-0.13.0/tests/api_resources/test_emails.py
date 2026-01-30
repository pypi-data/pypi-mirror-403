# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from ark import Ark, AsyncArk
from ark.types import (
    EmailListResponse,
    EmailSendResponse,
    EmailRetryResponse,
    EmailSendRawResponse,
    EmailRetrieveResponse,
    EmailSendBatchResponse,
    EmailRetrieveDeliveriesResponse,
)
from tests.utils import assert_matches_type
from ark.pagination import SyncPageNumberPagination, AsyncPageNumberPagination

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestEmails:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @parametrize
    def test_method_retrieve(self, client: Ark) -> None:
        email = client.emails.retrieve(
            email_id="emailId",
        )
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    def test_method_retrieve_with_all_params(self, client: Ark) -> None:
        email = client.emails.retrieve(
            email_id="emailId",
            expand="full",
        )
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    def test_raw_response_retrieve(self, client: Ark) -> None:
        response = client.emails.with_raw_response.retrieve(
            email_id="emailId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_retrieve(self, client: Ark) -> None:
        with client.emails.with_streaming_response.retrieve(
            email_id="emailId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailRetrieveResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            client.emails.with_raw_response.retrieve(
                email_id="",
            )

    @parametrize
    def test_method_list(self, client: Ark) -> None:
        email = client.emails.list()
        assert_matches_type(SyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    def test_method_list_with_all_params(self, client: Ark) -> None:
        email = client.emails.list(
            after="after",
            before="before",
            from_="dev@stainless.com",
            page=1,
            per_page=1,
            status="pending",
            tag="tag",
            to="dev@stainless.com",
        )
        assert_matches_type(SyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    def test_raw_response_list(self, client: Ark) -> None:
        response = client.emails.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(SyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    def test_streaming_response_list(self, client: Ark) -> None:
        with client.emails.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(SyncPageNumberPagination[EmailListResponse], email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_retrieve_deliveries(self, client: Ark) -> None:
        email = client.emails.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        )
        assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

    @parametrize
    def test_raw_response_retrieve_deliveries(self, client: Ark) -> None:
        response = client.emails.with_raw_response.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_retrieve_deliveries(self, client: Ark) -> None:
        with client.emails.with_streaming_response.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retrieve_deliveries(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            client.emails.with_raw_response.retrieve_deliveries(
                "",
            )

    @parametrize
    def test_method_retry(self, client: Ark) -> None:
        email = client.emails.retry(
            "emailId",
        )
        assert_matches_type(EmailRetryResponse, email, path=["response"])

    @parametrize
    def test_raw_response_retry(self, client: Ark) -> None:
        response = client.emails.with_raw_response.retry(
            "emailId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailRetryResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_retry(self, client: Ark) -> None:
        with client.emails.with_streaming_response.retry(
            "emailId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailRetryResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_path_params_retry(self, client: Ark) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            client.emails.with_raw_response.retry(
                "",
            )

    @parametrize
    def test_method_send(self, client: Ark) -> None:
        email = client.emails.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        )
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    def test_method_send_with_all_params(self, client: Ark) -> None:
        email = client.emails.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
            attachments=[
                {
                    "content": "content",
                    "content_type": "application/pdf",
                    "filename": "filename",
                }
            ],
            bcc=["dev@stainless.com"],
            cc=["dev@stainless.com"],
            headers={"foo": "string"},
            html="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
            metadata={
                "user_id": "usr_123",
                "campaign": "onboarding",
            },
            reply_to="dev@stainless.com",
            tag="tag",
            text="text",
            idempotency_key="user_123_order_456",
        )
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    def test_raw_response_send(self, client: Ark) -> None:
        response = client.emails.with_raw_response.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_send(self, client: Ark) -> None:
        with client.emails.with_streaming_response.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailSendResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_send_batch(self, client: Ark) -> None:
        email = client.emails.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        )
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    def test_method_send_batch_with_all_params(self, client: Ark) -> None:
        email = client.emails.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                    "html": "<p>Hi Alice, your order is ready!</p>",
                    "metadata": {
                        "user_id": "usr_123456",
                        "order_id": "ord_789012",
                        "campaign": "welcome_series",
                    },
                    "tag": "order-ready",
                    "text": "text",
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                    "html": "<p>Hi Bob, your order is ready!</p>",
                    "metadata": {
                        "user_id": "usr_123456",
                        "order_id": "ord_789012",
                        "campaign": "welcome_series",
                    },
                    "tag": "order-ready",
                    "text": "text",
                },
            ],
            from_="notifications@myapp.com",
            idempotency_key="user_123_order_456",
        )
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    def test_raw_response_send_batch(self, client: Ark) -> None:
        response = client.emails.with_raw_response.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_send_batch(self, client: Ark) -> None:
        with client.emails.with_streaming_response.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailSendBatchResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    def test_method_send_raw(self, client: Ark) -> None:
        email = client.emails.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        )
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    def test_method_send_raw_with_all_params(self, client: Ark) -> None:
        email = client.emails.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
            bounce=True,
        )
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    def test_raw_response_send_raw(self, client: Ark) -> None:
        response = client.emails.with_raw_response.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = response.parse()
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    def test_streaming_response_send_raw(self, client: Ark) -> None:
        with client.emails.with_streaming_response.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = response.parse()
            assert_matches_type(EmailSendRawResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncEmails:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @parametrize
    async def test_method_retrieve(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.retrieve(
            email_id="emailId",
        )
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    async def test_method_retrieve_with_all_params(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.retrieve(
            email_id="emailId",
            expand="full",
        )
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.retrieve(
            email_id="emailId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailRetrieveResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.retrieve(
            email_id="emailId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailRetrieveResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            await async_client.emails.with_raw_response.retrieve(
                email_id="",
            )

    @parametrize
    async def test_method_list(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.list()
        assert_matches_type(AsyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.list(
            after="after",
            before="before",
            from_="dev@stainless.com",
            page=1,
            per_page=1,
            status="pending",
            tag="tag",
            to="dev@stainless.com",
        )
        assert_matches_type(AsyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    async def test_raw_response_list(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(AsyncPageNumberPagination[EmailListResponse], email, path=["response"])

    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(AsyncPageNumberPagination[EmailListResponse], email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_retrieve_deliveries(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        )
        assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_retrieve_deliveries(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_retrieve_deliveries(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.retrieve_deliveries(
            "msg_12345_aBc123XyZ",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailRetrieveDeliveriesResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retrieve_deliveries(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            await async_client.emails.with_raw_response.retrieve_deliveries(
                "",
            )

    @parametrize
    async def test_method_retry(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.retry(
            "emailId",
        )
        assert_matches_type(EmailRetryResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_retry(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.retry(
            "emailId",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailRetryResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_retry(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.retry(
            "emailId",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailRetryResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_path_params_retry(self, async_client: AsyncArk) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `email_id` but received ''"):
            await async_client.emails.with_raw_response.retry(
                "",
            )

    @parametrize
    async def test_method_send(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        )
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    async def test_method_send_with_all_params(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
            attachments=[
                {
                    "content": "content",
                    "content_type": "application/pdf",
                    "filename": "filename",
                }
            ],
            bcc=["dev@stainless.com"],
            cc=["dev@stainless.com"],
            headers={"foo": "string"},
            html="<h1>Welcome!</h1><p>Thanks for signing up.</p>",
            metadata={
                "user_id": "usr_123",
                "campaign": "onboarding",
            },
            reply_to="dev@stainless.com",
            tag="tag",
            text="text",
            idempotency_key="user_123_order_456",
        )
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_send(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailSendResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_send(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.send(
            from_="Acme <hello@acme.com>",
            subject="Hello World",
            to=["user@example.com"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailSendResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_send_batch(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        )
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    async def test_method_send_batch_with_all_params(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                    "html": "<p>Hi Alice, your order is ready!</p>",
                    "metadata": {
                        "user_id": "usr_123456",
                        "order_id": "ord_789012",
                        "campaign": "welcome_series",
                    },
                    "tag": "order-ready",
                    "text": "text",
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                    "html": "<p>Hi Bob, your order is ready!</p>",
                    "metadata": {
                        "user_id": "usr_123456",
                        "order_id": "ord_789012",
                        "campaign": "welcome_series",
                    },
                    "tag": "order-ready",
                    "text": "text",
                },
            ],
            from_="notifications@myapp.com",
            idempotency_key="user_123_order_456",
        )
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_send_batch(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailSendBatchResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_send_batch(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.send_batch(
            emails=[
                {
                    "subject": "Hello Alice",
                    "to": ["alice@example.com"],
                },
                {
                    "subject": "Hello Bob",
                    "to": ["bob@example.com"],
                },
            ],
            from_="notifications@myapp.com",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailSendBatchResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True

    @parametrize
    async def test_method_send_raw(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        )
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    async def test_method_send_raw_with_all_params(self, async_client: AsyncArk) -> None:
        email = await async_client.emails.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
            bounce=True,
        )
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    async def test_raw_response_send_raw(self, async_client: AsyncArk) -> None:
        response = await async_client.emails.with_raw_response.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        email = await response.parse()
        assert_matches_type(EmailSendRawResponse, email, path=["response"])

    @parametrize
    async def test_streaming_response_send_raw(self, async_client: AsyncArk) -> None:
        async with async_client.emails.with_streaming_response.send_raw(
            from_="Acme <hello@acme.com>",
            raw_message="x",
            to=["user@example.com"],
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            email = await response.parse()
            assert_matches_type(EmailSendRawResponse, email, path=["response"])

        assert cast(Any, response.is_closed) is True
