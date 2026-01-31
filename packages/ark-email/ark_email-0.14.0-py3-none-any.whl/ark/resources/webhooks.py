# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import List, Optional
from typing_extensions import Literal

import httpx

from ..types import webhook_test_params, webhook_create_params, webhook_update_params, webhook_list_deliveries_params
from .._types import Body, Omit, Query, Headers, NotGiven, SequenceNotStr, omit, not_given
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.webhook_list_response import WebhookListResponse
from ..types.webhook_test_response import WebhookTestResponse
from ..types.webhook_create_response import WebhookCreateResponse
from ..types.webhook_delete_response import WebhookDeleteResponse
from ..types.webhook_update_response import WebhookUpdateResponse
from ..types.webhook_retrieve_response import WebhookRetrieveResponse
from ..types.webhook_list_deliveries_response import WebhookListDeliveriesResponse
from ..types.webhook_replay_delivery_response import WebhookReplayDeliveryResponse
from ..types.webhook_retrieve_delivery_response import WebhookRetrieveDeliveryResponse

__all__ = ["WebhooksResource", "AsyncWebhooksResource"]


class WebhooksResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> WebhooksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return WebhooksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> WebhooksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return WebhooksResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        name: str,
        url: str,
        all_events: Optional[bool] | Omit = omit,
        enabled: Optional[bool] | Omit = omit,
        events: Optional[
            List[
                Literal[
                    "MessageSent",
                    "MessageDelayed",
                    "MessageDeliveryFailed",
                    "MessageHeld",
                    "MessageBounced",
                    "MessageLinkClicked",
                    "MessageLoaded",
                    "DomainDNSError",
                ]
            ]
        ]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookCreateResponse:
        """
        Create a webhook endpoint to receive email event notifications.

        **Available events:**

        - `MessageSent` - Email accepted by recipient server
        - `MessageDeliveryFailed` - Delivery permanently failed
        - `MessageDelayed` - Delivery temporarily failed, will retry
        - `MessageBounced` - Email bounced
        - `MessageHeld` - Email held for review
        - `MessageLinkClicked` - Recipient clicked a link
        - `MessageLoaded` - Recipient opened the email
        - `DomainDNSError` - Domain DNS issue detected

        Args:
          name: Webhook name for identification

          url: HTTPS endpoint URL

          all_events: Subscribe to all events (ignores events array, accepts null)

          enabled: Whether the webhook is enabled (accepts null)

          events:
              Events to subscribe to (accepts null):

              - `MessageSent` - Email successfully delivered to recipient's server
              - `MessageDelayed` - Temporary delivery failure, will retry
              - `MessageDeliveryFailed` - Permanent delivery failure
              - `MessageHeld` - Email held for manual review
              - `MessageBounced` - Email bounced back
              - `MessageLinkClicked` - Recipient clicked a tracked link
              - `MessageLoaded` - Recipient opened the email (tracking pixel loaded)
              - `DomainDNSError` - DNS configuration issue detected

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return self._post(
            "/webhooks",
            body=maybe_transform(
                {
                    "name": name,
                    "url": url,
                    "all_events": all_events,
                    "enabled": enabled,
                    "events": events,
                },
                webhook_create_params.WebhookCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookCreateResponse,
        )

    def retrieve(
        self,
        webhook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookRetrieveResponse:
        """
        Get webhook details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return self._get(
            f"/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookRetrieveResponse,
        )

    def update(
        self,
        webhook_id: str,
        *,
        all_events: Optional[bool] | Omit = omit,
        enabled: Optional[bool] | Omit = omit,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        name: Optional[str] | Omit = omit,
        url: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookUpdateResponse:
        """
        Update a webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return self._patch(
            f"/webhooks/{webhook_id}",
            body=maybe_transform(
                {
                    "all_events": all_events,
                    "enabled": enabled,
                    "events": events,
                    "name": name,
                    "url": url,
                },
                webhook_update_params.WebhookUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookUpdateResponse,
        )

    def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookListResponse:
        """Get all configured webhook endpoints"""
        return self._get(
            "/webhooks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookListResponse,
        )

    def delete(
        self,
        webhook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookDeleteResponse:
        """
        Delete a webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return self._delete(
            f"/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookDeleteResponse,
        )

    def list_deliveries(
        self,
        webhook_id: str,
        *,
        after: int | Omit = omit,
        before: int | Omit = omit,
        event: Literal[
            "MessageSent",
            "MessageDelayed",
            "MessageDeliveryFailed",
            "MessageHeld",
            "MessageBounced",
            "MessageLinkClicked",
            "MessageLoaded",
            "DomainDNSError",
        ]
        | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        success: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookListDeliveriesResponse:
        """
        Get a paginated list of delivery attempts for a specific webhook.

        Use this to:

        - Monitor webhook health and delivery success rate
        - Debug failed deliveries
        - Find specific events to replay

        **Filtering:**

        - Filter by success/failure to find problematic deliveries
        - Filter by event type to find specific events
        - Filter by time range for debugging recent issues

        **Retry behavior:** Failed deliveries are automatically retried with exponential
        backoff over ~3 days. Check `willRetry` to see if more attempts are scheduled.

        Args:
          after: Only deliveries after this Unix timestamp

          before: Only deliveries before this Unix timestamp

          event: Filter by event type

          page: Page number (default 1)

          per_page: Items per page (default 30, max 100)

          success: Filter by delivery success (true = 2xx response, false = non-2xx or error)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return self._get(
            f"/webhooks/{webhook_id}/deliveries",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "event": event,
                        "page": page,
                        "per_page": per_page,
                        "success": success,
                    },
                    webhook_list_deliveries_params.WebhookListDeliveriesParams,
                ),
            ),
            cast_to=WebhookListDeliveriesResponse,
        )

    def replay_delivery(
        self,
        delivery_id: str,
        *,
        webhook_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookReplayDeliveryResponse:
        """
        Re-send a webhook delivery to your endpoint.

        **Use cases:**

        - Recover from transient failures after fixing your endpoint
        - Test endpoint changes with real historical data
        - Retry deliveries that failed due to downtime

        **How it works:**

        1. Fetches the original payload from the delivery
        2. Generates a new timestamp and signature
        3. Sends to your webhook URL immediately
        4. Returns the result (does not queue for retry if it fails)

        **Note:** The webhook must be enabled to replay deliveries.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        if not delivery_id:
            raise ValueError(f"Expected a non-empty value for `delivery_id` but received {delivery_id!r}")
        return self._post(
            f"/webhooks/{webhook_id}/deliveries/{delivery_id}/replay",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookReplayDeliveryResponse,
        )

    def retrieve_delivery(
        self,
        delivery_id: str,
        *,
        webhook_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookRetrieveDeliveryResponse:
        """
        Get detailed information about a specific webhook delivery attempt.

        Returns:

        - The complete request payload that was sent
        - Request headers including the signature
        - Response status code and body from your endpoint
        - Timing information

        Use this to debug why a delivery failed or verify what data was sent.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        if not delivery_id:
            raise ValueError(f"Expected a non-empty value for `delivery_id` but received {delivery_id!r}")
        return self._get(
            f"/webhooks/{webhook_id}/deliveries/{delivery_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookRetrieveDeliveryResponse,
        )

    def test(
        self,
        webhook_id: str,
        *,
        event: Literal[
            "MessageSent",
            "MessageDelayed",
            "MessageDeliveryFailed",
            "MessageHeld",
            "MessageBounced",
            "MessageLinkClicked",
            "MessageLoaded",
            "DomainDNSError",
        ],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookTestResponse:
        """
        Send a test payload to your webhook endpoint and verify it receives the data
        correctly.

        Use this to:

        - Verify your webhook URL is accessible
        - Test your signature verification code
        - Ensure your server handles the payload format correctly

        **Test payload format:** The test payload is identical to real webhook payloads,
        containing sample data for the specified event type. Your webhook should respond
        with a 2xx status code.

        Args:
          event: Event type to simulate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return self._post(
            f"/webhooks/{webhook_id}/test",
            body=maybe_transform({"event": event}, webhook_test_params.WebhookTestParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookTestResponse,
        )


class AsyncWebhooksResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncWebhooksResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#accessing-raw-response-data-eg-headers
        """
        return AsyncWebhooksResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncWebhooksResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/ArkHQ-io/ark-python#with_streaming_response
        """
        return AsyncWebhooksResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        name: str,
        url: str,
        all_events: Optional[bool] | Omit = omit,
        enabled: Optional[bool] | Omit = omit,
        events: Optional[
            List[
                Literal[
                    "MessageSent",
                    "MessageDelayed",
                    "MessageDeliveryFailed",
                    "MessageHeld",
                    "MessageBounced",
                    "MessageLinkClicked",
                    "MessageLoaded",
                    "DomainDNSError",
                ]
            ]
        ]
        | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookCreateResponse:
        """
        Create a webhook endpoint to receive email event notifications.

        **Available events:**

        - `MessageSent` - Email accepted by recipient server
        - `MessageDeliveryFailed` - Delivery permanently failed
        - `MessageDelayed` - Delivery temporarily failed, will retry
        - `MessageBounced` - Email bounced
        - `MessageHeld` - Email held for review
        - `MessageLinkClicked` - Recipient clicked a link
        - `MessageLoaded` - Recipient opened the email
        - `DomainDNSError` - Domain DNS issue detected

        Args:
          name: Webhook name for identification

          url: HTTPS endpoint URL

          all_events: Subscribe to all events (ignores events array, accepts null)

          enabled: Whether the webhook is enabled (accepts null)

          events:
              Events to subscribe to (accepts null):

              - `MessageSent` - Email successfully delivered to recipient's server
              - `MessageDelayed` - Temporary delivery failure, will retry
              - `MessageDeliveryFailed` - Permanent delivery failure
              - `MessageHeld` - Email held for manual review
              - `MessageBounced` - Email bounced back
              - `MessageLinkClicked` - Recipient clicked a tracked link
              - `MessageLoaded` - Recipient opened the email (tracking pixel loaded)
              - `DomainDNSError` - DNS configuration issue detected

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        return await self._post(
            "/webhooks",
            body=await async_maybe_transform(
                {
                    "name": name,
                    "url": url,
                    "all_events": all_events,
                    "enabled": enabled,
                    "events": events,
                },
                webhook_create_params.WebhookCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookCreateResponse,
        )

    async def retrieve(
        self,
        webhook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookRetrieveResponse:
        """
        Get webhook details

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return await self._get(
            f"/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookRetrieveResponse,
        )

    async def update(
        self,
        webhook_id: str,
        *,
        all_events: Optional[bool] | Omit = omit,
        enabled: Optional[bool] | Omit = omit,
        events: Optional[SequenceNotStr[str]] | Omit = omit,
        name: Optional[str] | Omit = omit,
        url: Optional[str] | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookUpdateResponse:
        """
        Update a webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return await self._patch(
            f"/webhooks/{webhook_id}",
            body=await async_maybe_transform(
                {
                    "all_events": all_events,
                    "enabled": enabled,
                    "events": events,
                    "name": name,
                    "url": url,
                },
                webhook_update_params.WebhookUpdateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookUpdateResponse,
        )

    async def list(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookListResponse:
        """Get all configured webhook endpoints"""
        return await self._get(
            "/webhooks",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookListResponse,
        )

    async def delete(
        self,
        webhook_id: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookDeleteResponse:
        """
        Delete a webhook

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return await self._delete(
            f"/webhooks/{webhook_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookDeleteResponse,
        )

    async def list_deliveries(
        self,
        webhook_id: str,
        *,
        after: int | Omit = omit,
        before: int | Omit = omit,
        event: Literal[
            "MessageSent",
            "MessageDelayed",
            "MessageDeliveryFailed",
            "MessageHeld",
            "MessageBounced",
            "MessageLinkClicked",
            "MessageLoaded",
            "DomainDNSError",
        ]
        | Omit = omit,
        page: int | Omit = omit,
        per_page: int | Omit = omit,
        success: bool | Omit = omit,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookListDeliveriesResponse:
        """
        Get a paginated list of delivery attempts for a specific webhook.

        Use this to:

        - Monitor webhook health and delivery success rate
        - Debug failed deliveries
        - Find specific events to replay

        **Filtering:**

        - Filter by success/failure to find problematic deliveries
        - Filter by event type to find specific events
        - Filter by time range for debugging recent issues

        **Retry behavior:** Failed deliveries are automatically retried with exponential
        backoff over ~3 days. Check `willRetry` to see if more attempts are scheduled.

        Args:
          after: Only deliveries after this Unix timestamp

          before: Only deliveries before this Unix timestamp

          event: Filter by event type

          page: Page number (default 1)

          per_page: Items per page (default 30, max 100)

          success: Filter by delivery success (true = 2xx response, false = non-2xx or error)

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return await self._get(
            f"/webhooks/{webhook_id}/deliveries",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "after": after,
                        "before": before,
                        "event": event,
                        "page": page,
                        "per_page": per_page,
                        "success": success,
                    },
                    webhook_list_deliveries_params.WebhookListDeliveriesParams,
                ),
            ),
            cast_to=WebhookListDeliveriesResponse,
        )

    async def replay_delivery(
        self,
        delivery_id: str,
        *,
        webhook_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookReplayDeliveryResponse:
        """
        Re-send a webhook delivery to your endpoint.

        **Use cases:**

        - Recover from transient failures after fixing your endpoint
        - Test endpoint changes with real historical data
        - Retry deliveries that failed due to downtime

        **How it works:**

        1. Fetches the original payload from the delivery
        2. Generates a new timestamp and signature
        3. Sends to your webhook URL immediately
        4. Returns the result (does not queue for retry if it fails)

        **Note:** The webhook must be enabled to replay deliveries.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        if not delivery_id:
            raise ValueError(f"Expected a non-empty value for `delivery_id` but received {delivery_id!r}")
        return await self._post(
            f"/webhooks/{webhook_id}/deliveries/{delivery_id}/replay",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookReplayDeliveryResponse,
        )

    async def retrieve_delivery(
        self,
        delivery_id: str,
        *,
        webhook_id: str,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookRetrieveDeliveryResponse:
        """
        Get detailed information about a specific webhook delivery attempt.

        Returns:

        - The complete request payload that was sent
        - Request headers including the signature
        - Response status code and body from your endpoint
        - Timing information

        Use this to debug why a delivery failed or verify what data was sent.

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        if not delivery_id:
            raise ValueError(f"Expected a non-empty value for `delivery_id` but received {delivery_id!r}")
        return await self._get(
            f"/webhooks/{webhook_id}/deliveries/{delivery_id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookRetrieveDeliveryResponse,
        )

    async def test(
        self,
        webhook_id: str,
        *,
        event: Literal[
            "MessageSent",
            "MessageDelayed",
            "MessageDeliveryFailed",
            "MessageHeld",
            "MessageBounced",
            "MessageLinkClicked",
            "MessageLoaded",
            "DomainDNSError",
        ],
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = not_given,
    ) -> WebhookTestResponse:
        """
        Send a test payload to your webhook endpoint and verify it receives the data
        correctly.

        Use this to:

        - Verify your webhook URL is accessible
        - Test your signature verification code
        - Ensure your server handles the payload format correctly

        **Test payload format:** The test payload is identical to real webhook payloads,
        containing sample data for the specified event type. Your webhook should respond
        with a 2xx status code.

        Args:
          event: Event type to simulate

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
        """
        if not webhook_id:
            raise ValueError(f"Expected a non-empty value for `webhook_id` but received {webhook_id!r}")
        return await self._post(
            f"/webhooks/{webhook_id}/test",
            body=await async_maybe_transform({"event": event}, webhook_test_params.WebhookTestParams),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=WebhookTestResponse,
        )


class WebhooksResourceWithRawResponse:
    def __init__(self, webhooks: WebhooksResource) -> None:
        self._webhooks = webhooks

        self.create = to_raw_response_wrapper(
            webhooks.create,
        )
        self.retrieve = to_raw_response_wrapper(
            webhooks.retrieve,
        )
        self.update = to_raw_response_wrapper(
            webhooks.update,
        )
        self.list = to_raw_response_wrapper(
            webhooks.list,
        )
        self.delete = to_raw_response_wrapper(
            webhooks.delete,
        )
        self.list_deliveries = to_raw_response_wrapper(
            webhooks.list_deliveries,
        )
        self.replay_delivery = to_raw_response_wrapper(
            webhooks.replay_delivery,
        )
        self.retrieve_delivery = to_raw_response_wrapper(
            webhooks.retrieve_delivery,
        )
        self.test = to_raw_response_wrapper(
            webhooks.test,
        )


class AsyncWebhooksResourceWithRawResponse:
    def __init__(self, webhooks: AsyncWebhooksResource) -> None:
        self._webhooks = webhooks

        self.create = async_to_raw_response_wrapper(
            webhooks.create,
        )
        self.retrieve = async_to_raw_response_wrapper(
            webhooks.retrieve,
        )
        self.update = async_to_raw_response_wrapper(
            webhooks.update,
        )
        self.list = async_to_raw_response_wrapper(
            webhooks.list,
        )
        self.delete = async_to_raw_response_wrapper(
            webhooks.delete,
        )
        self.list_deliveries = async_to_raw_response_wrapper(
            webhooks.list_deliveries,
        )
        self.replay_delivery = async_to_raw_response_wrapper(
            webhooks.replay_delivery,
        )
        self.retrieve_delivery = async_to_raw_response_wrapper(
            webhooks.retrieve_delivery,
        )
        self.test = async_to_raw_response_wrapper(
            webhooks.test,
        )


class WebhooksResourceWithStreamingResponse:
    def __init__(self, webhooks: WebhooksResource) -> None:
        self._webhooks = webhooks

        self.create = to_streamed_response_wrapper(
            webhooks.create,
        )
        self.retrieve = to_streamed_response_wrapper(
            webhooks.retrieve,
        )
        self.update = to_streamed_response_wrapper(
            webhooks.update,
        )
        self.list = to_streamed_response_wrapper(
            webhooks.list,
        )
        self.delete = to_streamed_response_wrapper(
            webhooks.delete,
        )
        self.list_deliveries = to_streamed_response_wrapper(
            webhooks.list_deliveries,
        )
        self.replay_delivery = to_streamed_response_wrapper(
            webhooks.replay_delivery,
        )
        self.retrieve_delivery = to_streamed_response_wrapper(
            webhooks.retrieve_delivery,
        )
        self.test = to_streamed_response_wrapper(
            webhooks.test,
        )


class AsyncWebhooksResourceWithStreamingResponse:
    def __init__(self, webhooks: AsyncWebhooksResource) -> None:
        self._webhooks = webhooks

        self.create = async_to_streamed_response_wrapper(
            webhooks.create,
        )
        self.retrieve = async_to_streamed_response_wrapper(
            webhooks.retrieve,
        )
        self.update = async_to_streamed_response_wrapper(
            webhooks.update,
        )
        self.list = async_to_streamed_response_wrapper(
            webhooks.list,
        )
        self.delete = async_to_streamed_response_wrapper(
            webhooks.delete,
        )
        self.list_deliveries = async_to_streamed_response_wrapper(
            webhooks.list_deliveries,
        )
        self.replay_delivery = async_to_streamed_response_wrapper(
            webhooks.replay_delivery,
        )
        self.retrieve_delivery = async_to_streamed_response_wrapper(
            webhooks.retrieve_delivery,
        )
        self.test = async_to_streamed_response_wrapper(
            webhooks.test,
        )
